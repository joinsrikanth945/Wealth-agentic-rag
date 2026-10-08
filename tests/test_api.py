import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app

client = TestClient(app)


def path_for(endpoint):
    """Find the full path of an endpoint, whatever prefix the router uses.

    Uses the app's OpenAPI schema, so it works regardless of how FastAPI
    stores included routers internally.
    """
    for path in app.openapi()["paths"]:
        if path.endswith(endpoint):
            return path
    raise AssertionError(f"No route ending in {endpoint}")


def admin_key():
    return routes.settings.admin_api_key


# ---------- Health ----------

def test_health_returns_ok():
    response = client.get(path_for("/health"))
    assert response.status_code == 200


# ---------- Chat ----------

def test_chat_without_a_body_is_rejected():
    response = client.post(path_for("/chat"))
    assert response.status_code == 422


def test_chat_returns_500_when_the_agent_fails(mocker):
    mocker.patch.object(
        routes, "ask", side_effect=RuntimeError("LLM unavailable"))
    response = client.post(
        path_for("/chat"), json={"question": "How do I reset MFA?"})
    assert response.status_code == 500


# ---------- Ingest (document upload) ----------

def upload(filename, content=b"Sample text for testing.", key=None):
    headers = {"x-admin-key": key} if key is not None else {}
    files = {"file": (filename, content, "text/plain")}
    return client.post(path_for("/ingest"), files=files, headers=headers)


def test_upload_rejected_without_admin_key():
    response = upload("guide.txt")
    assert response.status_code == 401


def test_upload_rejected_with_wrong_admin_key():
    response = upload("guide.txt", key="definitely-wrong-key")
    assert response.status_code == 401


def test_upload_rejects_unsupported_file_type():
    response = upload("virus.exe", key=admin_key())
    assert response.status_code == 400
    assert "Supported" in response.json()["detail"]


def test_upload_of_supported_file_is_indexed(mocker):
    if not hasattr(routes, "add_documents"):
        pytest.skip("routes.py does not import add_documents directly")
    fake_store = mocker.patch.object(
        routes, "add_documents", return_value=["id-1", "id-2"])
    response = upload("guide.txt", key=admin_key())
    assert response.status_code == 200
    fake_store.assert_called_once()


# ---------- Home page ----------

def test_home_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text.lower()
