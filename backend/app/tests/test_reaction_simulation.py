import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_simulate_hydrogenation_success(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": [
                {
                    "canonical_smiles": "C=C",
                    "coefficient": 1,
                }
            ],
            "reagents": [],
            "reaction_type": "hydrogenation",
            "conditions": None,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "simulated"
    assert data["reaction_type"] == "hydrogenation"

    assert len(data["product_sets"]) == 1
    assert data["product_sets"][0]["products"][0]["canonical_smiles"] == "CC"

    assert len(data["mappings"]) == 1

    mapping = data["mappings"][0]

    assert len(mapping["atom_mappings"]) == 2
    assert mapping["broken_bonds"] == []
    assert mapping["formed_bonds"] == []

    assert len(mapping["changed_bonds"]) == 1

    changed_bond = mapping["changed_bonds"][0]

    assert changed_bond["old_bond_order"] == 2.0
    assert changed_bond["new_bond_order"] == 1.0


def test_simulate_unsupported_reaction_type(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": [
                {
                    "canonical_smiles": "CCO",
                    "coefficient": 1,
                }
            ],
            "reaction_type": "metathesis",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "unsupported"
    assert data["product_sets"] == []
    assert data["mappings"] == []


def test_simulate_incorrect_reactant_count(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": [
                {
                    "canonical_smiles": "C=C",
                    "coefficient": 1,
                },
                {
                    "canonical_smiles": "CC",
                    "coefficient": 1,
                },
            ],
            "reaction_type": "hydrogenation",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["product_sets"] == []
    assert data["mappings"] == []


def test_simulate_no_reaction(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": [
                {
                    "canonical_smiles": "CC",
                    "coefficient": 1,
                }
            ],
            "reaction_type": "hydrogenation",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "no_reaction"
    assert data["product_sets"] == []
    assert data["mappings"] == []


def test_simulate_invalid_molecule(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": [
                {
                    "canonical_smiles": "not_a_smiles",
                    "coefficient": 1,
                }
            ],
            "reaction_type": "hydrogenation",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["category"] == "invalid_molecule_error"


def test_simulate_rejects_invalid_coefficient(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": [
                {
                    "canonical_smiles": "C=C",
                    "coefficient": 0,
                }
            ],
            "reaction_type": "hydrogenation",
        },
    )

    assert response.status_code == 422


def test_simulate_rejects_malformed_request(client):
    response = client.post(
        "/api/reactions/simulate",
        json={
            "reactants": "C=C",
            "reaction_type": "hydrogenation",
        },
    )

    assert response.status_code == 422
