import shutil

import pytest


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract OCR executable is not installed")
def test_document_analyze_real_ocr(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as f:
        r = client.post("/api/v1/documents/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"document": ("doc.png", f, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert "John" in body["ocr_text"]
    assert body["extracted_fields"].get("document_number")
    assert body["model_type"] == "REAL_MODEL"
    assert 0 <= body["ocr_confidence"] <= 1
    assert 0 <= body["document_score"] <= 100


def test_document_analyze_without_tesseract_returns_warning(client, analyst_token, demo_dir, monkeypatch):
    from app.services import document_service

    def tesseract_missing(*args, **kwargs):
        raise document_service.pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(document_service.pytesseract, "image_to_data", tesseract_missing)
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as f:
        r = client.post("/api/v1/documents/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                        files={"document": ("doc.png", f, "image/png")})

    assert r.status_code == 200
    body = r.json()
    assert body["ocr_text"] == ""
    assert body["model_type"] == "HEURISTIC"
    assert any("Tesseract OCR is not installed" in anomaly for anomaly in body["anomalies"])


def test_pdf_document_is_converted_to_first_page_png():
    import pymupdf
    from app.services.document_service import normalize_document_image

    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "IDENTITY DOCUMENT")
    pdf_bytes = pdf.tobytes()
    pdf.close()

    image_bytes = normalize_document_image(pdf_bytes, "document.pdf")

    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_document_analyze_continues_after_ocr_timeout(client, analyst_token, demo_dir, monkeypatch):
    from app.services import document_service

    def tesseract_timeout(*args, **kwargs):
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(document_service.pytesseract, "image_to_data", tesseract_timeout)
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as f:
        response = client.post(
            "/api/v1/documents/analyze",
            headers={"Authorization": f"Bearer {analyst_token}"},
            files={"document": ("doc.png", f, "image/png")},
        )

    assert response.status_code == 200
    assert any("OCR timed out" in item for item in response.json()["anomalies"])


def test_document_analyze_empty_file_rejected(client, analyst_token):
    r = client.post("/api/v1/documents/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                     files={"document": ("empty.png", b"", "image/png")})
    assert r.status_code == 400


def test_document_analyze_requires_auth(client, demo_dir):
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as f:
        r = client.post("/api/v1/documents/analyze", files={"document": ("doc.png", f, "image/png")})
    assert r.status_code == 401
