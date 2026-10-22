import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app


def test_extract_text_txt():
    client = TestClient(app)
    content = b"Aceasta este o notificare importanta pentru prima zi de lucru."
    files = {"file": ("nota.txt", io.BytesIO(content), "text/plain")}
    res = client.post("/api/extract-text", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "notificare importanta" in data["data"]["text"]
    assert data["data"]["format"] == "txt"
    assert data["data"]["needs_ocr"] is False


def test_extract_text_html():
    client = TestClient(app)
    html_bytes = b"<html><head><style>body{color:red}</style></head><body><h1>Titlu document</h1><p>Paragraf cu instruc&#539;iuni.</p><script>alert(1)</script></body></html>"
    files = {"file": ("pagina.html", io.BytesIO(html_bytes), "text/html")}
    res = client.post("/api/extract-text", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "Titlu document" in data["data"]["text"]
    assert "alert" not in data["data"]["text"]
    assert data["data"]["format"] == "html"


def test_extract_text_docx():
    client = TestClient(app)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p><w:r><w:t>Procedura de integrare a angajatilor.</w:t></w:r></w:p>
          </w:body>
        </w:document>"""
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))

    docx_bytes = buf.getvalue()
    files = {
        "file": (
            "manual.docx",
            io.BytesIO(docx_bytes),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    res = client.post("/api/extract-text", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "Procedura de integrare" in data["data"]["text"]
    assert data["data"]["format"] == "docx"


def test_extract_text_empty_file():
    client = TestClient(app)
    files = {"file": ("gol.txt", io.BytesIO(b"   "), "text/plain")}
    res = client.post("/api/extract-text", files=files)
    assert res.status_code == 400
    data = res.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "empty_input"


def test_extract_text_file_too_large():
    client = TestClient(app)
    # 10 MB + 1 byte
    oversized = b"x" * (10 * 1024 * 1024 + 10)
    files = {"file": ("mare.txt", io.BytesIO(oversized), "text/plain")}
    res = client.post("/api/extract-text", files=files)
    assert res.status_code == 400
    data = res.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "too_large"
