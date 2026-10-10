def test_deepfake_analyze_image(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/images/face_a_1.png", "rb") as f:
        r = client.post("/api/v1/deepfake/analyze?media_type=IMAGE",
                         headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"file": ("a1.png", f, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["model_type"] == "HEURISTIC"
    assert "human review" in body["disclaimer"].lower()
    assert 0 <= body["deepfake_probability"] <= 1


def test_deepfake_analyze_video(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/videos/demo_clip_1.mp4", "rb") as f:
        r = client.post("/api/v1/deepfake/analyze?media_type=VIDEO",
                         headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"file": ("clip.mp4", f, "video/mp4")})
    assert r.status_code == 200
    body = r.json()
    assert len(body["frame_results"]) > 0
    assert "fps" in body["metadata"]


def test_deepfake_invalid_media_type(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/images/face_a_1.png", "rb") as f:
        r = client.post("/api/v1/deepfake/analyze?media_type=AUDIO",
                         headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"file": ("a1.png", f, "image/png")})
    assert r.status_code == 422


def test_voice_analyze(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/audio/demo_voice_1.wav", "rb") as f:
        r = client.post("/api/v1/voice/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"audio": ("v.wav", f, "audio/wav")})
    assert r.status_code == 200
    body = r.json()
    assert body["transcript_model_type"] == "DEMO_SIMULATION"
    assert body["duration_seconds"] > 0
    assert body["decision"] in ("ACCEPTED", "REVIEW_REQUIRED", "REJECTED")


def test_voice_analyze_corrupt_file_rejected_at_upload_validation(client, analyst_token):
    # File-security validation (magic-byte sniff) catches this before it ever
    # reaches the voice service -- this is the correct, earlier failure point.
    r = client.post("/api/v1/voice/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                     files={"audio": ("bad.wav", b"not a real wav file", "audio/wav")})
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_voice_analyze_valid_container_bad_payload_rejected_by_service(client, analyst_token):
    # A RIFF/WAVE-shaped header that isn't valid PCM data passes upload
    # validation but should be rejected by the service's own wave parser.
    fake_wav = b"RIFF____WAVEfmt _______________data____" + b"\x00" * 20
    r = client.post("/api/v1/voice/analyze", headers={"Authorization": f"Bearer {analyst_token}"},
                     files={"audio": ("bad.wav", fake_wav, "audio/wav")})
    assert r.status_code == 200
    assert r.json()["decision"] == "REJECTED"


def test_trust_compute_case_a_low_risk(client, analyst_token):
    payload = {"identity_score": 0.9, "biometric_score": 0.9, "liveness_score": 0.9, "document_score": 0.9,
               "fraud_signal_count": 0}
    r = client.post("/api/v1/trust/compute", headers={"Authorization": f"Bearer {analyst_token}"}, json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] == "LOW"
    assert body["trust_score"] >= 70


def test_trust_compute_case_b_high_risk(client, analyst_token):
    payload = {"identity_score": 0.2, "biometric_score": 0.2, "liveness_score": 0.2, "document_score": 0.2,
               "fraud_signal_count": 3, "face_mismatch": True, "low_liveness": True}
    r = client.post("/api/v1/trust/compute", headers={"Authorization": f"Bearer {analyst_token}"}, json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] in ("HIGH", "CRITICAL")


def test_fraud_scan_and_list(client, analyst_token):
    r = client.post("/api/v1/fraud/scan", headers={"Authorization": f"Bearer {analyst_token}"})
    assert r.status_code == 200
    r2 = client.get("/api/v1/fraud/cases", headers={"Authorization": f"Bearer {analyst_token}"})
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_graph_analytics(client, analyst_token):
    r = client.get("/api/v1/graph/analytics", headers={"Authorization": f"Bearer {analyst_token}"})
    assert r.status_code == 200
    body = r.json()
    assert "node_count" in body and "edge_count" in body


def test_alerts_list_and_update(client, analyst_token):
    r = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {analyst_token}"})
    assert r.status_code == 200
    alerts = r.json()
    if alerts:
        alert_id = alerts[0]["id"]
        r2 = client.patch(f"/api/v1/alerts/{alert_id}/status", headers={"Authorization": f"Bearer {analyst_token}"},
                            json={"status": "INVESTIGATING"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "INVESTIGATING"


def test_alerts_invalid_status_rejected(client, analyst_token):
    r = client.patch("/api/v1/alerts/1/status", headers={"Authorization": f"Bearer {analyst_token}"},
                       json={"status": "NOT_A_STATUS"})
    assert r.status_code == 422


def test_audit_logs_listable(client, analyst_token):
    r = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {analyst_token}"})
    assert r.status_code == 200
    logs = r.json()
    assert any(log["action"] == "LOGIN" for log in logs)


def test_copilot_insufficient_evidence(client, analyst_token):
    r = client.post("/api/v1/copilot/ask", headers={"Authorization": f"Bearer {analyst_token}"},
                     json={"question": "Why is user 999999 high risk?"})
    assert r.status_code == 200
    assert "insufficient evidence" in r.json()["answer"].lower()


def test_models_status_labels_every_component(client, viewer_token):
    r = client.get("/api/v1/models/status", headers={"Authorization": f"Bearer {viewer_token}"})
    assert r.status_code == 200
    models = r.json()["models"]
    assert len(models) >= 5
    for m in models:
        assert m["model_type"] in ("REAL_MODEL", "HEURISTIC", "DEMO_SIMULATION")


def test_health_endpoints(client):
    for path in ["/health", "/health/database", "/health/redis", "/health/kafka",
                  "/health/neo4j", "/health/models"]:
        r = client.get(path)
        assert r.status_code == 200, path
