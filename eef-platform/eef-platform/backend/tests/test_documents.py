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


def test_document_analyze_empty_file_rejected(client, analyst_token):
    r = client.post("/api/v1/documents/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                     files={"document": ("empty.png", b"", "image/png")})
    assert r.status_code == 400


def test_document_analyze_requires_auth(client, demo_dir):
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as f:
        r = client.post("/api/v1/documents/analyze", files={"document": ("doc.png", f, "image/png")})
    assert r.status_code == 401
