def test_face_match_same_person(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/images/face_a_1.png", "rb") as ref, open(f"{demo_dir}/images/face_a_2.png", "rb") as cmp:
        r = client.post("/api/v1/face/match", headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"reference": ("a1.png", ref, "image/png"), "comparison": ("a2.png", cmp, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["model_type"] == "HEURISTIC"
    assert "threshold_used" in body
    assert body["match_decision"] is True


def test_face_match_missing_face(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/images/face_a_1.png", "rb") as ref, open(f"{demo_dir}/images/face_b_1.png", "rb") as cmp:
        r = client.post("/api/v1/face/match", headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"reference": ("a1.png", ref, "image/png"), "comparison": ("b1.png", cmp, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["match_decision"] is False


def test_liveness_challenge_generation(client):
    r = client.get("/api/v1/face/liveness/challenge?steps=3")
    assert r.status_code == 200
    body = r.json()
    assert len(body["challenge"]) == 3
    assert "prototype" in body["note"].lower()


def test_liveness_passive(client, analyst_token, demo_dir):
    with open(f"{demo_dir}/images/face_a_1.png", "rb") as f:
        r = client.post("/api/v1/face/liveness/passive", headers={"Authorization": f"Bearer {analyst_token}"},
                         files={"image": ("a1.png", f, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["model_type"] == "HEURISTIC"
    assert 0 <= body["liveness_score"] <= 1
