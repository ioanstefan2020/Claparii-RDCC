import io
import zipfile

import pytest
from app.ingest import (
    IngestError,
    detect_language_and_situation,
    extract_text_from_file,
)


def test_ingest_plain_text():
    content = "Aceasta este o notificare oficială trimisă către cetățean.".encode(
        "utf-8"
    )
    text, fmt = extract_text_from_file(content, filename="notificare.txt")
    assert fmt == "txt"
    assert "notificare oficială" in text


def test_ingest_markdown():
    content = "# Titlu Document\n\n- Pasul 1: Mergi la primărie\n- Pasul 2: Depune actul".encode(
        "utf-8"
    )
    text, fmt = extract_text_from_file(content, filename="instructiuni.md")
    assert fmt == "md"
    assert "Pasul 1" in text


def test_ingest_docx():
    # Build a valid in-memory .docx zip file
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p><w:r><w:t>Contract individual de muncă.</w:t></w:r></w:p>
                <w:p><w:r><w:t>Salariatul începe activitatea la 1 noiembrie.</w:t></w:r></w:p>
            </w:body>
        </w:document>
        """
        zf.writestr("word/document.xml", doc_xml)
        zf.writestr("[Content_Types].xml", "<Types/>")

    docx_bytes = buf.getvalue()
    text, fmt = extract_text_from_file(docx_bytes, filename="contract.docx")
    assert fmt == "docx"
    assert "Contract individual de muncă" in text
    assert "1 noiembrie" in text


def test_ingest_eml():
    raw_email = (
        "From: manager@firma.ro\n"
        "To: angajat@firma.ro\n"
        "Subject: Sedinta de luni ora 10\n"
        "Date: Thu, 22 Oct 2026 10:00:00 +0300\n"
        "Content-Type: text/plain; charset=utf-8\n\n"
        "Buna ziua,\nVa rog sa pregatiti raportul de activitate pana vineri.\nMultumesc!"
    ).encode("utf-8")

    text, fmt = extract_text_from_file(raw_email, filename="mesaj.eml")
    assert fmt == "eml"
    assert "Sedinta de luni ora 10" in text
    assert "raportul de activitate" in text


def test_ingest_corrupted_file():
    bad_docx = b"PK\x03\x04this_is_not_a_valid_zip"
    with pytest.raises(IngestError) as exc_info:
        extract_text_from_file(bad_docx, filename="defect.docx")
    assert exc_info.value.code in ("corrupted_file", "unsupported_type")


def test_ingest_file_too_large():
    too_large = b"A" * (10 * 1024 * 1024 + 100)
    with pytest.raises(IngestError) as exc_info:
        extract_text_from_file(too_large, filename="mare.txt")
    assert exc_info.value.code == "file_too_large"


def test_detect_language_and_situation():
    # Official letter
    res_off = detect_language_and_situation(
        "Către Primăria Sectorului 3, vă solicităm declarația de impunere fiscală și taxa de timbru."
    )
    assert res_off["language"] == "ro"
    assert res_off["situation"] in ("official", "work")
    assert res_off["confidence"] > 0.5

    # English work task
    res_en = detect_language_and_situation(
        "Please submit your sprint velocity report by Friday afternoon."
    )
    assert res_en["language"] == "en"
    assert res_en["situation"] == "work"
