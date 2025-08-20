"""
Stage-1: Terminal tabanlı Kütüphane uygulaması için OOP yapıları

Sınıflar:
- Book: Bir kitabı temsil eder
- Library: Kitap koleksiyonunu yönetir ve JSON dosyasına kalıcı olarak yazar/okur
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional


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
        """JSON dosyasından kitapları yükler. Dosya yoksa sessizce boş liste ile devam eder."""
        if not self.storage_path.exists():
            self._books = []
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                # Beklenmeyen formatta ise sıfırla
                self._books = []
                return
            self._books = [Book.from_dict(item) for item in raw]
        except Exception:
            # Bozuk dosya durumunda veri kaybını önlemek için belleği temiz başlat
            self._books = []

    def save_books(self) -> None:
        """Kitap listesini JSON dosyasına yazar."""
        data = [b.to_dict() for b in self._books]
        self.storage_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # İşlevsel metotlar
    def add_book(self, book: Book) -> None:
        """Yeni bir kitabı ekler ve dosyayı günceller. ISBN benzersiz kabul edilir."""
        if any(existing.isbn == book.isbn for existing in self._books):
            raise ValueError(f"ISBN already exists: {book.isbn}")
        self._books.append(book)
        self.save_books()

    def remove_book(self, isbn: str) -> None:
        """ISBN'e göre kitabı siler ve dosyayı günceller. Bulunamazsa hata fırlatır."""
        original_len = len(self._books)
        self._books = [b for b in self._books if b.isbn != isbn]
        if len(self._books) == original_len:
            raise ValueError(f"Book not found for ISBN: {isbn}")
        self.save_books()

    def list_books(self) -> List[Book]:
        """Tüm kitapları döndürür."""
        return list(self._books)

    def find_book(self, isbn: str) -> Optional[Book]:
        """ISBN ile kitabı bulur; yoksa None döner."""
        for book in self._books:
            if book.isbn == isbn:
                return book
        return None


