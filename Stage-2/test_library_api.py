from pathlib import Path
import sys

# Stage-2 klasörünü import yoluna ekle
CURRENT_DIR = Path(__file__).parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from library import Library, Book  # noqa: E402


def test_add_book_by_isbn_success(monkeypatch, tmp_path: Path):
    store = tmp_path / "lib.json"
    lib = Library(store)

    # Sıralı çağrılar: 1) kitap detayı, 2) yazar detayı
    calls = {"count": 0}

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    def fake_get(url, timeout=10, headers=None):
        calls["count"] += 1
        if calls["count"] == 1:
            # Book endpoint response
            return MockResponse(
                200,
                {
                    "title": "Dune",
                    "authors": [{"key": "/authors/OL123A"}],
                },
            )
        else:
            # Author endpoint response
            return MockResponse(200, {"name": "Frank Herbert"})

    import httpx

    monkeypatch.setattr(httpx, "get", fake_get)

    book = lib.add_book_by_isbn("9780441013593")
    assert isinstance(book, Book)
    assert book.title == "Dune"
    assert book.author == "Frank Herbert"
    # Persist kontrolü
    lib2 = Library(store)
    lib2.load_books()
    assert lib2.find_book("9780441013593") is not None


def test_add_book_by_isbn_not_found(monkeypatch, tmp_path: Path):
    store = tmp_path / "lib.json"
    lib = Library(store)

    class MockResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}
        def json(self):
            return self._payload

    def fake_get(url, timeout=10, headers=None):
        return MockResponse(404, {})

    import httpx
    monkeypatch.setattr(httpx, "get", fake_get)

    try:
        lib.add_book_by_isbn("0000000000")
        assert False, "Beklenen hata yükseltilmedi"
    except ValueError as e:
        assert "404" in str(e)


def test_add_book_by_isbn_network_error(monkeypatch, tmp_path: Path):
    store = tmp_path / "lib.json"
    lib = Library(store)

    import httpx

    def fake_get(url, timeout=10, headers=None):
        raise httpx.RequestError("network down")

    monkeypatch.setattr(httpx, "get", fake_get)

    try:
        lib.add_book_by_isbn("9780441013593")
        assert False, "Beklenen hata yükseltilmedi"
    except ValueError as e:
        assert "Ağ hatası" in str(e)
