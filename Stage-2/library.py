"""
Stage-2: Open Library API ile ISBN'den kitap bilgisi çekerek ekleme

Bu aşamada Stage-1'in tüm yetenekleri korunur. Ek olarak:
- add_book_by_isbn(isbn): Open Library'den başlık ve yazar(lar)ı çekip ekler

Not: Open Library, sık isteklerde User-Agent header'ı talep eder.
Bkz: https://openlibrary.org/developers/api
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

import httpx


DEFAULT_UA = (
    "GlobalAIHub-Python202-Stage2/1.0 (+contact@example.com)"
)


class Book:
    """Kütüphanedeki tek bir kitabı temsil eder."""

    def __init__(self, title: str, author: str, isbn: str):
        self.title = title
        self.author = author
        self.isbn = isbn

    def __str__(self) -> str:
        return f"{self.title} by {self.author} (ISBN: {self.isbn})"

    def to_dict(self) -> dict:
        return {"title": self.title, "author": self.author, "isbn": self.isbn}

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        return cls(title=data["title"], author=data["author"], isbn=data["isbn"])


class Library:
    """Kitap koleksiyonunu yöneten sınıf. Verileri JSON dosyasında kalıcı tutar."""

    def __init__(self, storage_path: str | Path = "library.json"):
        self.storage_path = Path(storage_path)
        self._books: List[Book] = []

    # Persistans yardımcıları
    def load_books(self) -> None:
        if not self.storage_path.exists():
            self._books = []
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                self._books = []
                return
            self._books = [Book.from_dict(item) for item in raw]
        except Exception:
            self._books = []

    def save_books(self) -> None:
        data = [b.to_dict() for b in self._books]
        self.storage_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Stage-1 metodları
    def add_book(self, book: Book) -> None:
        if any(existing.isbn == book.isbn for existing in self._books):
            raise ValueError(f"ISBN already exists: {book.isbn}")
        self._books.append(book)
        self.save_books()

    def remove_book(self, isbn: str) -> None:
        original_len = len(self._books)
        self._books = [b for b in self._books if b.isbn != isbn]
        if len(self._books) == original_len:
            raise ValueError(f"Book not found for ISBN: {isbn}")
        self.save_books()

    def list_books(self) -> List[Book]:
        return list(self._books)

    def find_book(self, isbn: str) -> Optional[Book]:
        for book in self._books:
            if book.isbn == isbn:
                return book
        return None

    # Stage-2: Open Library entegrasyonu
    def add_book_by_isbn(self, isbn: str, *, user_agent: str = DEFAULT_UA) -> Book:
        """Open Library API'den verileri çekerek kitabı ekler.

        Başarısızlık durumunda ValueError yükseltir.
        """
        if any(existing.isbn == isbn for existing in self._books):
            raise ValueError(f"ISBN already exists: {isbn}")

        try:
            title, authors = self._fetch_book_metadata(isbn, user_agent=user_agent)
        except Exception as exc:  # httpx hataları veya parse hataları
            raise ValueError(str(exc))

        author_str = ", ".join(authors) if authors else "Unknown"
        book = Book(title=title, author=author_str, isbn=isbn)
        self._books.append(book)
        self.save_books()
        return book

    @staticmethod
    def _fetch_book_metadata(isbn: str, *, user_agent: str = DEFAULT_UA) -> Tuple[str, List[str]]:
        base = "https://openlibrary.org"
        url = f"{base}/isbn/{isbn}.json"
        headers = {"User-Agent": user_agent}
        try:
            resp = httpx.get(url, timeout=10, headers=headers)
        except httpx.RequestError as e:
            raise ValueError("Ağ hatası: Open Library API'ye ulaşılamıyor.") from e

        if resp.status_code == 404:
            raise ValueError("Kitap bulunamadı (404).")
        if resp.status_code >= 400:
            raise ValueError(f"Open Library API hata döndü: {resp.status_code}")

        data = resp.json()
        title = data.get("title")
        if not title:
            raise ValueError("API yanıtı geçersiz: 'title' alanı yok.")

        authors: List[str] = []
        author_refs = data.get("authors") or []
        for ref in author_refs:
            key = ref.get("key")
            if not key:
                continue
            # Her yazar için isim verisini çekmeyi dene
            try:
                a_resp = httpx.get(f"{base}{key}.json", timeout=10, headers=headers)
                if a_resp.status_code == 200:
                    a_data = a_resp.json()
                    name = a_data.get("name")
                    if name:
                        authors.append(name)
            except httpx.RequestError:
                # Yazar ismini çekemezsek es geçip diğerlerine devam edelim
                continue

        # Yazar isimleri hiç çekilemediyse by_statement gibi alanlardan düşmeye çalışabiliriz
        if not authors:
            by_stmt = data.get("by_statement")
            if by_stmt:
                authors = [by_stmt]

        return title, authors

