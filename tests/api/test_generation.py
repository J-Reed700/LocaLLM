import pytest
from fastapi.testclient import TestClient
from websrc.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_generate_text():
    response = client.post("/htmx/generate/text/", data={
        "prompt": "Hello, world!",
        "max_length": 100
    })
    assert response.status_code == 200
    assert "Generated text based on prompt" in response.text
