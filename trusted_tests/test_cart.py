"""Independent business oracle. Not writable through model tools."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"items": [{"unit_amount": 125, "quantity": 3}]}, 375),
        (
            {
                "items": [
                    {"unit_amount": 79, "quantity": 7},
                    {"unit_amount": 20, "quantity": 2},
                ]
            },
            593,
        ),
        ({"items": [{"unit_amount": 150, "quantity": 1}]}, 150),
        ({"items": []}, 0),
        ({"items": None}, 0),
        ({}, 0),
    ],
)
def test_cart_behavior(payload, expected):
    with TestClient(app) as client:
        response = client.post("/cart/total", json=payload)
    assert response.status_code == 200
    assert response.json() == {"total_minor": expected}


def test_invalid_quantity_is_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/cart/total", json={"items": [{"unit_amount": 125, "quantity": -1}]}
        )
    assert response.status_code == 422
