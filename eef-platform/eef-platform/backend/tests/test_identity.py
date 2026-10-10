def test_full_verification_pipeline(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as doc, \
         open(f"{demo_dir}/images/face_a_1.png", "rb") as selfie:
        r = client.post(
            "/api/v1/identity/verify",
            headers={"Authorization": f"Bearer {analyst_token}"},
            data={"full_name": "Test Person One", "document_type": "NATIONAL_ID",
                   "email": "test1@example.test"},
            files={"document": ("doc.png", doc, "image/png"), "selfie": ("selfie.png", selfie, "image/png")},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ["verification_id", "status", "identity_match_score", "liveness_score",
                 "document_score", "risk_score", "trust_score", "fraud_indicators", "explanation", "timestamp"]:
        assert key in body
    assert body["status"] in ("VERIFIED", "REVIEW_REQUIRED", "REJECTED")
    assert "decision_reasoning" in body["explanation"]


def test_verification_invalid_document_type(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/documents/demo_national_id_1.png", "rb") as doc, \
         open(f"{demo_dir}/images/face_a_1.png", "rb") as selfie:
        r = client.post(
            "/api/v1/identity/verify",
            headers={"Authorization": f"Bearer {analyst_token}"},
            data={"full_name": "Bad Doc Type", "document_type": "NOT_A_REAL_TYPE"},
            files={"document": ("doc.png", doc, "image/png"), "selfie": ("selfie.png", selfie, "image/png")},
        )
    assert r.status_code == 422


def test_verification_missing_file(client, analyst_token):
    r = client.post(
        "/api/v1/identity/verify",
        headers={"Authorization": f"Bearer {analyst_token}"},
        data={"full_name": "No File", "document_type": "NATIONAL_ID"},
    )
    assert r.status_code == 422  # FastAPI validation: required files missing


def test_verification_unsupported_format(client, analyst_token, demo_dir, tmp_path):
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("not an image")
    with open(f"{demo_dir}/images/face_a_1.png", "rb") as selfie, open(bad_file, "rb") as doc:
        r = client.post(
            "/api/v1/identity/verify",
            headers={"Authorization": f"Bearer {analyst_token}"},
            data={"full_name": "Bad Format", "document_type": "NATIONAL_ID"},
            files={"document": ("bad.txt", doc, "text/plain"), "selfie": ("selfie.png", selfie, "image/png")},
        )
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_get_verification_not_found(client, analyst_token):
    r = client.get("/api/v1/identity/999999", headers={"Authorization": f"Bearer {analyst_token}"})
    assert r.status_code == 404
