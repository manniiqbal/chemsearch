import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_renders_real_svg(client):
    response = client.post(
        "/api/molecules/render",
        json={"smiles": "C(C)O", "width": 320, "height": 220},
    )
    assert response.status_code == 200
    assert response.json()["canonical_smiles"] == "CCO"
    assert "<svg" in response.json()["svg"]


def test_rejects_invalid_smiles(client):
    response = client.post("/api/molecules/render", json={"smiles": "not-smiles"})
    assert response.status_code == 400
    assert response.json()["category"] == "invalid_molecule_error"


def test_lists_curated_rules(client):
    response = client.get("/api/reactions/rules")
    assert response.status_code == 200
    assert len(response.json()) == 11
