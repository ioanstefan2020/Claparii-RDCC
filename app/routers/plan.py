from __future__ import annotations

import datetime
import re
import urllib.parse
import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

from app.config import settings
from app.guardrails import verify_quotes
from app.llm import generate_json
from app.prompts.plan import MOCK, SYSTEM, build_user
from app.schemas.common import AppError, MetaInfo, SuccessEnvelope
from app.schemas.plan import PlanExtractData, PlanExtractRequest, PlanTask

router = APIRouter(prefix="/api/plan", tags=["plan"])


class CalendarLinkRequest(BaseModel):
    title: str = Field(
        ..., max_length=200, description="Titlul sarcinii sau al evenimentului"
    )
    date_iso: str | None = Field(None, description="Data în format YYYY-MM-DD")
    due_iso: str | None = Field(None, description="Alias pentru date_iso")
    time_start: str | None = Field(
        None, description="Ora de început opțională în format HH:MM"
    )
    due_time: str | None = Field(None, description="Alias pentru time_start")
    duration_minutes: int = Field(60, ge=5, le=1440)
    details: str | None = Field(None, max_length=2000)
    description: str | None = Field(None, max_length=2000)
    location: str | None = Field(None, max_length=300)

    @model_validator(mode="after")
    def sync_aliases(self) -> CalendarLinkRequest:
        if not self.date_iso and self.due_iso:
            self.date_iso = self.due_iso
        if not self.time_start and self.due_time:
            self.time_start = self.due_time
        if not self.details and self.description:
            self.details = self.description
        if not self.date_iso:
            self.date_iso = datetime.date.today().isoformat()
        return self


class CalendarLinkResponse(BaseModel):
    google_calendar_url: str
    ics_content: str
    suggested_filename: str
    ics_filename: str | None = None
    reminder_minutes: int = 30
    title: str | None = None
    due_iso: str | None = None
    start_iso: str | None = None

    @model_validator(mode="after")
    def sync_response_aliases(self) -> CalendarLinkResponse:
        if not self.ics_filename:
            self.ics_filename = self.suggested_filename
        return self


@router.post("/extract", response_model=SuccessEnvelope[PlanExtractData])
async def extract_plan(payload: PlanExtractRequest):
    text = payload.text.strip()
    if not text:
        raise AppError(
            code="empty_input",
            message_ro="Textul este gol. Lipește sau scrie ceva.",
            status_code=400,
        )

    if len(text) > settings.MAX_INPUT_CHARS:
        raise AppError(
            code="too_long",
            message_ro=f"Textul depășește limita permisă de {settings.MAX_INPUT_CHARS} caractere.",
            status_code=400,
        )

    user_prompt = build_user(
        text=text, today_iso=payload.today_iso, profile=payload.profile
    )

    data_model, meta = await generate_json(
        task="plan_extract",
        system=SYSTEM,
        user=user_prompt,
        schema=PlanExtractData,
        mock=MOCK,
    )

    # Convert tasks to dicts for quote verification guardrail
    raw_tasks = [task.model_dump() for task in data_model.tasks]
    kept_tasks, dropped_tasks = verify_quotes(raw_tasks, text, key="source_quote")

    warnings = list(meta.get("warnings", []))
    if dropped_tasks:
        count = len(dropped_tasks)
        warnings.append(
            f"{count} {'sarcină eliminată' if count == 1 else 'sarcini eliminate'}: citatul nu apare în text."
        )

    # Re-key IDs t1..tn
    validated_tasks: list[PlanTask] = []
    for idx, t in enumerate(kept_tasks, start=1):
        t["id"] = f"t{idx}"
        validated_tasks.append(PlanTask.model_validate(t))

    clean_data = PlanExtractData(tasks=validated_tasks)

    meta_info = MetaInfo(
        provider=meta.get("provider", "mock"),
        cached=meta.get("cached", False),
        warnings=warnings,
        ai_notice_ro=meta.get(
            "ai_notice_ro", "Generat de AI — verifică datele importante."
        ),
    )

    return SuccessEnvelope(ok=True, data=clean_data, meta=meta_info)


@router.post("/calendar-link", response_model=SuccessEnvelope[CalendarLinkResponse])
async def generate_calendar_link(payload: CalendarLinkRequest):
    """Generates 1-click Google Calendar URL and RFC 5545 iCalendar (.ics) content."""
    clean_date = payload.date_iso.replace("-", "").strip()

    start_str = ""
    end_str = ""
    dates_param = ""

    if payload.time_start and re.match(r"^\d{1,2}:\d{2}$", payload.time_start.strip()):
        parts = payload.time_start.strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        try:
            start_dt = datetime.datetime.strptime(
                f"{payload.date_iso} {h:02d}:{m:02d}", "%Y-%m-%d %H:%M"
            )
            end_dt = start_dt + datetime.timedelta(minutes=payload.duration_minutes)
            start_str = start_dt.strftime("%Y%m%dT%H%M%S")
            end_str = end_dt.strftime("%Y%m%dT%H%M%S")
            dates_param = f"{start_str}/{end_str}"
        except Exception:
            dates_param = f"{clean_date}/{clean_date}"
    else:
        try:
            dt = datetime.datetime.strptime(payload.date_iso, "%Y-%m-%d")
            next_dt = dt + datetime.timedelta(days=1)
            dates_param = f"{dt.strftime('%Y%m%d')}/{next_dt.strftime('%Y%m%d')}"
        except Exception:
            dates_param = f"{clean_date}/{clean_date}"

    params = {
        "action": "TEMPLATE",
        "text": payload.title,
        "dates": dates_param,
        "details": payload.details or "Sarcina extrasă din PrimaZi",
        "location": payload.location or "",
    }
    google_calendar_url = (
        f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
    )

    # RFC 5545 iCalendar content
    uid = f"{uuid.uuid4().hex[:12]}@primazi.local"
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    ics_dtstart = (
        f"DTSTART:{start_str}" if start_str else f"DTSTART;VALUE=DATE:{clean_date}"
    )
    ics_dtend = f"DTEND:{end_str}" if end_str else f"DTEND;VALUE=DATE:{clean_date}"

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PrimaZi//Accesibilitate RO//RO",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc}",
        ics_dtstart,
        ics_dtend,
        f"SUMMARY:{payload.title}",
        f"DESCRIPTION:{payload.details or 'Sarcina extrasă din PrimaZi'}",
        f"LOCATION:{payload.location or ''}",
        "STATUS:CONFIRMED",
        "BEGIN:VALARM",
        "TRIGGER:-PT60M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Memento sarcină PrimaZi: {payload.title}",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_content = "\r\n".join(ics_lines)
    clean_slug = re.sub(r"[^a-zA-Z0-9]+", "_", payload.title[:30]).strip("_")
    filename = f"sarcină_{clean_slug}_{clean_date}.ics"

    resp = CalendarLinkResponse(
        google_calendar_url=google_calendar_url,
        ics_content=ics_content,
        suggested_filename=filename,
        reminder_minutes=60,
    )
    meta_info = MetaInfo(
        provider="system",
        cached=False,
        warnings=[],
        ai_notice_ro="Generat automat pentru integrare în calendar.",
    )
    return SuccessEnvelope(ok=True, data=resp, meta=meta_info)
