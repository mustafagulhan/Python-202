from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi.testclient import TestClient  # type: ignore

from app import app, storage_file, lib


def setup_module(module):
    # Temiz bir depoyla başla
    if storage_file.exists():
        storage_file.unlink()
    lib.load_books()


client = TestClient(app)


def test_crud_flow():
    # boş liste
    r = client.get("/books")
    assert r.status_code == 200
    assert r.json() == []

    # create manuel
    payload = {"title": "Test", "author": "Author", "isbn": "9780441013593"}
    r = client.post("/books", json=payload)
    assert r.status_code == 201

    # get
    r = client.get(f"/books/{payload['isbn']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Test"

    # update
    r = client.put(f"/books/{payload['isbn']}", json={"title": "Updated"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"

    # delete
    r = client.delete(f"/books/{payload['isbn']}")
    assert r.status_code == 204

    # not found
    r = client.get(f"/books/{payload['isbn']}")
    assert r.status_code == 404


