"""Unit and integration tests for Nexus Campus Intelligence, Vault & Serendipity endpoints."""

import pytest
from starlette.testclient import TestClient

from services.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_vault_seal_hypothesis(client):
    """Verifies cryptographic proof-of-priority sealing and certificate generation."""
    payload = {
        "title": "Quantum Error Correction on Distributed Edge Micro-controllers",
        "hypothesis_text": "Evaluating surface code syndrome extraction using quantized tensor networks under high thermal noise.",
        "author_id": "anurag_mscs_26",
        "department": "Computer Science",
        "degree_level": "MSCS '26"
    }
    response = client.post("/api/v2/campus/vault/seal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "certificate_id" in data
    assert data["certificate_id"].startswith("NX-")
    assert len(data["fingerprint"]) == 64  # Valid SHA-256 hex
    assert data["status"] == "SEALED"
    assert data["anchor_network"] == "Base Sepolia"

    # Verify certificate via verification endpoint
    cert_id = data["certificate_id"]
    verify_resp = client.get(f"/api/v2/campus/vault/verify/{cert_id}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True


def test_vault_verify_standard_certificate(client):
    """Verifies that seed certificates (e.g. NX-8492) verify successfully."""
    response = client.get("/api/v2/campus/vault/verify/NX-8492")
    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert data["certificate_id"] == "NX-8492"


def test_list_campus_projects(client):
    """Verifies campus project listing and privacy masking with preview_as."""
    response = client.get("/api/v2/campus/projects?preview_as=peer")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 3
    # Check that each project has offers and needs
    for p in projects:
        assert len(p["offers"]) > 0
        assert len(p["needs"]) > 0
        assert p["full_hypothesis"] is None  # Private details masked for peers


def test_serendipity_matches(client):
    """Verifies AI serendipity matchmaking and bridge sentences."""
    response = client.get("/api/v2/campus/serendipity/matches")
    assert response.status_code == 200
    matches = response.json()
    assert len(matches) >= 2
    top_match = matches[0]
    assert top_match["synergy_score"] >= 80
    assert len(top_match["bridge_sentence"]) > 20
    assert top_match["meta_reasoning_tokens"] > 0


def test_serendipity_mutual_reveal(client):
    """Verifies double opt-in mutual reveal between matched researchers."""
    response = client.post("/api/v2/campus/serendipity/reveal?match_id=match_01")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MUTUALLY_REVEALED"
    assert "peer_contact" in data
    assert "WATERMARKED" in data["audit_watermark"]


def test_pixel_proof_claim_verification(client):
    """Verifies SAM 3.1 polygon grounding and Muse Wonder verification."""
    payload = {
        "claim_text": "The distributed consensus protocol achieves 94% throughput under 40% packet drops.",
        "source_id": "heming_merlins_whisper",
        "page_number": 4
    }
    response = client.post("/api/v2/campus/proof/verify-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verification_status"] == "VERIFIED"
    assert "bounding_box" in data
    assert len(data["sam_mask_polygon"]) == 4
    assert data["tokens_used"]["reasoning_tokens"] > 0


def test_meta_ai_telemetry(client):
    """Verifies live Meta AI model telemetry and token metrics."""
    response = client.get("/api/v2/campus/meta-ai/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["models"]["frontier_reasoning"] == "muse-wonder-1.0"
    assert data["build_telemetry"]["total_tokens_processed"] > 100000
