import email
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


class IngestError(Exception):
    def __init__(
        self, code: str, message_ro: str, message_en: str, status_code: int = 400
    ):
        super().__init__(message_ro)
        self.code = code
        self.message_ro = message_ro
        self.message_en = message_en
        self.status_code = status_code


def extract_text_from_file(
    content: bytes, filename: str, content_type: str | None = None
) -> tuple[str, str]:
    """
    Extracts text safely from user-supplied file bytes (.txt, .md, .docx, .pdf, .eml).
    Enforces maximum size (10 MB), validates file headers/magic bytes, and prevents macro execution.
    Returns (extracted_text, detected_format).
    """
    if len(content) > MAX_UPLOAD_SIZE:
        raise IngestError(
            code="file_too_large",
            message_ro="Fișierul depășește limita maximă permisă de 10 MB.",
            message_en="File exceeds the maximum allowed size of 10 MB.",
            status_code=400,
        )

    if not content or len(content.strip()) == 0:
        raise IngestError(
            code="empty_input",
            message_ro="Fișierul încărcat este gol.",
            message_en="Uploaded file is empty.",
            status_code=400,
        )

    lower_name = filename.lower()

    # 1. Plain text and Markdown
    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        fmt = "md" if lower_name.endswith(".md") else "txt"
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1250"):
            try:
                decoded = content.decode(enc).strip()
                if not decoded:
                    raise IngestError(
                        code="empty_input",
                        message_ro="Fișierul text nu conține caractere lizibile.",
                        message_en="Text file does not contain readable characters.",
                    )
                return decoded, fmt
            except UnicodeDecodeError:
                continue
        raise IngestError(
            code="corrupted_file",
            message_ro="Fișierul text nu a putut fi decodat.",
            message_en="Text file encoding could not be decoded.",
        )

    # 2. DOCX (OpenXML ZIP archive)
    if lower_name.endswith(".docx"):
        if not content.startswith(b"PK\x03\x04"):
            raise IngestError(
                code="unsupported_type",
                message_ro="Fișierul specificat nu este un document .docx valid (lipsesc semnăturile ZIP).",
                message_en="Specified file is not a valid .docx document (ZIP signature missing).",
            )
        try:
            buf = io.BytesIO(content)
            with zipfile.ZipFile(buf, "r") as zf:
                # Security: never execute any macros, verify document.xml
                if "word/document.xml" not in zf.namelist():
                    raise IngestError(
                        code="corrupted_file",
                        message_ro="Documentul Word este deteriorat (lipsește document.xml).",
                        message_en="Word document is corrupted (document.xml missing).",
                    )
                xml_content = zf.read("word/document.xml")
                root = ET.fromstring(xml_content)

                # Word XML namespace for text elements
                ns = {
                    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                }
                paragraphs = []
                for p in root.findall(".//w:p", ns):
                    texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
                    if texts:
                        paragraphs.append("".join(texts))

                extracted = "\n\n".join(paragraphs).strip()
                if not extracted:
                    raise IngestError(
                        code="empty_input",
                        message_ro="Documentul .docx nu conține text extras.",
                        message_en="The .docx document contains no readable text.",
                    )
                return extracted, "docx"
        except zipfile.BadZipFile:
            raise IngestError(
                code="corrupted_file",
                message_ro="Fișierul .docx este arhivat defectuos sau corupt.",
                message_en="The .docx file archive is invalid or corrupted.",
            )
        except IngestError:
            raise
        except Exception as e:
            raise IngestError(
                code="corrupted_file",
                message_ro=f"Eroare la parsarea documentului Word: {e}",
                message_en=f"Error parsing Word document: {e}",
            )

    # 3. PDF (Portable Document Format)
    if lower_name.endswith(".pdf") or content.startswith(b"%PDF-"):
        if not content.startswith(b"%PDF-"):
            raise IngestError(
                code="unsupported_type",
                message_ro="Fișierul nu conține semnătura standard PDF.",
                message_en="File does not contain standard PDF signature.",
            )
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = []
            for p in reader.pages:
                txt = p.extract_text()
                if txt:
                    pages_text.append(txt)
            extracted = "\n\n".join(pages_text).strip()
            if not extracted:
                raise IngestError(
                    code="empty_input",
                    message_ro="Fișierul PDF nu conține text selectabil (este posibil să fie o imagine scanată fără OCR).",
                    message_en="PDF contains no selectable text (may be a scanned image).",
                )
            return extracted, "pdf"
        except IngestError:
            raise
        except Exception as e:
            raise IngestError(
                code="corrupted_file",
                message_ro=f"Fișierul PDF este deteriorat sau parolat: {e}",
                message_en=f"PDF file is corrupted or password-protected: {e}",
            )

    # 4. EML (RFC 822 Email Message)
    if (
        lower_name.endswith(".eml")
        or b"From:" in content[:200]
        or b"Subject:" in content[:200]
    ):
        try:
            msg = email.message_from_bytes(content)
            body_parts = []
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_parts.append(payload.decode("utf-8", errors="replace"))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode("utf-8", errors="replace"))

            subj = msg.get("Subject", "")
            sender = msg.get("From", "")
            date_str = msg.get("Date", "")

            header_info = f"Subiect: {subj}\nExpeditor: {sender}\nData: {date_str}\n\n"
            full_text = header_info + "\n".join(body_parts)
            clean_text = full_text.strip()
            if len(clean_text) < 10:
                raise IngestError(
                    code="empty_input",
                    message_ro="E-mailul nu conține text în corpul mesajului.",
                    message_en="Email message body contains no readable text.",
                )
            return clean_text, "eml"
        except IngestError:
            raise
        except Exception as e:
            raise IngestError(
                code="corrupted_file",
                message_ro=f"Eroare la procesarea e-mailului .eml: {e}",
                message_en=f"Error processing .eml email file: {e}",
            )

    raise IngestError(
        code="unsupported_type",
        message_ro=f"Formatul fișierului '{filename}' nu este suportat. Formate acceptate: .txt, .md, .docx, .pdf, .eml.",
        message_en=f"File format '{filename}' is not supported. Accepted formats: .txt, .md, .docx, .pdf, .eml.",
    )


def detect_language_and_situation(text: str) -> dict[str, Any]:
    """
    Detects language (ro/en) and situation (work, official, contract, school, medical)
    with a confidence score based on lexical analysis.
    """
    lower = text.lower()

    # 1. Language detection
    ro_markers = [
        "și",
        "sau",
        "pentru",
        "este",
        "sunt",
        "care",
        "cu",
        "la",
        "în",
        "de",
        "vă",
        "rugăm",
        "trebuie",
        "aveți",
    ]
    en_markers = [
        "the",
        "and",
        "for",
        "with",
        "please",
        "should",
        "submit",
        "from",
        "your",
        "project",
        "meeting",
    ]

    ro_count = sum(
        1 for w in ro_markers if re.search(r"\b" + re.escape(w) + r"\b", lower)
    )
    en_count = sum(
        1 for w in en_markers if re.search(r"\b" + re.escape(w) + r"\b", lower)
    )

    lang = "ro" if ro_count >= en_count else "en"

    # 2. Situation detection
    official_keywords = [
        "primăria",
        "primarie",
        "anaf",
        "impozit",
        "taxa",
        "timbr",
        "notificare",
        "penalitate",
        "amendă",
        "ghiseul",
        "contestație",
        "sector",
        "impunere",
    ]
    contract_keywords = [
        "contract",
        "clauză",
        "clauze",
        "salariat",
        "angajator",
        "reziliere",
        "articolul",
        "obligații",
        "durata contractului",
        "încetare",
    ]
    school_keywords = [
        "curs",
        "facultate",
        "profesor",
        "examen",
        "notă",
        "temă",
        "syllabus",
        "student",
        "universitate",
        "credite",
    ]
    medical_keywords = [
        "rețetă",
        "medic",
        "tratament",
        "farmacie",
        "dozaj",
        "diagnostic",
        "medicament",
        "clinică",
    ]
    work_keywords = [
        "onboarding",
        "ședință",
        "sedinta",
        "sprint",
        "task",
        "coleg",
        "echipă",
        "echipa",
        "raport",
        "deadline",
        "manager",
        "proiect",
    ]

    scores = {
        "official": sum(2 for k in official_keywords if k in lower),
        "contract": sum(2 for k in contract_keywords if k in lower),
        "school": sum(2 for k in school_keywords if k in lower),
        "medical": sum(2 for k in medical_keywords if k in lower),
        "work": sum(1 for k in work_keywords if k in lower) + 1,  # baseline work
    }

    best_sit = max(scores.items(), key=lambda item: item[1])
    situation = best_sit[0]
    total_score = sum(scores.values()) or 1
    confidence = min(0.98, max(0.65, round(best_sit[1] / total_score + 0.35, 2)))

    return {
        "language": lang,
        "situation": situation,
        "confidence": confidence,
    }


def compute_readability_metrics(text: str) -> dict[str, Any]:
    """
    Computes deterministic readability metrics for Romanian text:
    Average Sentence Length (ASL), Average Syllables per Word (ASW),
    and adapted Flesch Reading Ease score (0 to 100).
    """
    if not text.strip():
        return {
            "sentence_count": 0,
            "word_count": 0,
            "readability_score": 50.0,
        }

    sentences = [s.strip() for s in re.split(r"[.?!]+", text) if s.strip()]
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    sentence_count = max(1, len(sentences))

    asl = word_count / sentence_count

    vowels = set("aăâeiîouyAĂÂEIÎOUY")
    syllables = sum(sum(1 for char in word if char in vowels) for word in words)
    asw = (syllables / word_count) if word_count > 0 else 1.0

    # Romanian calibrated Flesch-Kincaid formula
    score = 206.835 - (1.015 * asl) - (65.0 * asw)
    score_clamped = round(max(10.0, min(100.0, score)), 1)

    return {
        "sentence_count": sentence_count,
        "word_count": word_count,
        "readability_score": score_clamped,
    }


def mask_pii(text: str) -> tuple[str, dict[str, str]]:
    """
    Masks sensitive personal data (CNP, Romanian IBAN, phone, email)
    before sending to external LLMs or logs (Task P1-12).
    Returns (masked_text, mapping_dict).
    """
    mapping: dict[str, str] = {}
    counter = 1

    def replace_val(tag_prefix: str, val: str) -> str:
        nonlocal counter
        placeholder = f"[{tag_prefix}_{counter}]"
        mapping[placeholder] = val
        counter += 1
        return placeholder

    # 1. Romanian CNP (13 consecutive digits starting with 1-8)
    def cnp_repl(match):
        val = match.group(0)
        # Check digit validation (weights 279146358279)
        weights = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
        total = sum(int(val[i]) * weights[i] for i in range(12))
        ctrl = total % 11
        if ctrl == 10:
            ctrl = 1
        if ctrl == int(val[12]):
            return replace_val("CNP", val)
        return val

    masked = re.sub(r"\b[1-8]\d{12}\b", cnp_repl, text)

    # 2. Romanian IBAN (RO + 2 digits + 4 letters + 16 alphanumeric)
    masked = re.sub(
        r"\bRO\d{2}[A-Z]{4}[0-9A-Z]{16}\b",
        lambda m: replace_val("IBAN", m.group(0)),
        masked,
        flags=re.IGNORECASE,
    )

    # 3. Romanian Phone numbers (+407... or 07...)
    masked = re.sub(
        r"\b(?:\+40|0040|0)7\d{8}\b",
        lambda m: replace_val("PHONE", m.group(0)),
        masked,
    )

    # 4. Email addresses
    masked = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        lambda m: replace_val("EMAIL", m.group(0)),
        masked,
    )

    return masked, mapping


def unmask_pii(text: str, mapping: dict[str, str]) -> str:
    """Restores masked PII tokens to their original values."""
    res = text
    for placeholder, original in mapping.items():
        res = res.replace(placeholder, original)
    return res
