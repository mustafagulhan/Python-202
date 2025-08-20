"""
Stage-3: FastAPI ile Kendi API'n

Uç noktalar:
- GET    /books                 → tüm kitapları listele (sayfalı)
- GET    /books/{isbn}          → ISBN'e göre tek kitap
- POST   /books                 → body ile kitap ekle
- POST   /books/isbn/{isbn}     → Open Library'den çekerek ekle
- PUT    /books/{isbn}          → kitabı güncelle (başlık/yazar)
- DELETE /books/{isbn}          → kitabı sil

Kalıcı depolama: Stage-3/library.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
from fastapi import FastAPI, HTTPException, status, Query, Path as FPath
from pydantic import BaseModel, Field


DEFAULT_UA = "GlobalAIHub-Python202-Stage3/1.0 (+contact@example.com)"


class Book(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=10)


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=10)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    author: Optional[str] = Field(default=None, min_length=1)


class Library:
    def __init__(self, storage_path: str | Path):
        self.storage_path = Path(storage_path)
        self._books: List[Book] = []

    def load_books(self) -> None:
        if not self.storage_path.exists():
            self._books = []
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                self._books = []
                return
            self._books = [Book(**item) for item in raw]
        except Exception:
            self._books = []

    def save_books(self) -> None:
        data = [b.model_dump() for b in self._books]
        self.storage_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def list_books(self) -> List[Book]:
        return list(self._books)

    def find_book(self, isbn: str) -> Optional[Book]:
        for b in self._books:
            if b.isbn == isbn:
                return b
        return None

    def add_book(self, book: Book) -> None:
        if self.find_book(book.isbn) is not None:
            raise ValueError("ISBN zaten mevcut")
        self._books.append(book)
        self.save_books()

    def remove_book(self, isbn: str) -> None:
        before = len(self._books)
        self._books = [b for b in self._books if b.isbn != isbn]
        if len(self._books) == before:
            raise ValueError("Kitap bulunamadı")
        self.save_books()

    def update_book(self, isbn: str, update: BookUpdate) -> Book:
        book = self.find_book(isbn)
        if book is None:
            raise ValueError("Kitap bulunamadı")
        new_book = book.model_copy(update={
            "title": update.title if update.title is not None else book.title,
            "author": update.author if update.author is not None else book.author,
        })
        # replace
        self._books = [new_book if b.isbn == isbn else b for b in self._books]
        self.save_books()
        return new_book

    def add_book_by_isbn(self, isbn: str, *, user_agent: str = DEFAULT_UA) -> Book:
        if self.find_book(isbn) is not None:
            raise ValueError("ISBN zaten mevcut")
        title, authors = fetch_book_metadata(isbn, user_agent=user_agent)
        author_str = ", ".join(authors) if authors else "Unknown"
        book = Book(title=title, author=author_str, isbn=isbn)
        self._books.append(book)
        self.save_books()
        return book


def fetch_book_metadata(isbn: str, *, user_agent: str = DEFAULT_UA) -> Tuple[str, List[str]]:
    base = "https://openlibrary.org"
    url = f"{base}/isbn/{isbn}.json"
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    try:
        resp = httpx.get(url, timeout=10, headers=headers)
    except httpx.RequestError as e:
        raise ValueError("Ağ hatası: Open Library API'ye ulaşılamıyor.") from e

    if 300 <= resp.status_code < 400:
        location = resp.headers.get("location") or resp.headers.get("Location")
        if location:
            try:
                resp = httpx.get(location, timeout=10, headers=headers)
            except httpx.RequestError as e:
                raise ValueError("Ağ hatası: Open Library yönlendirme başarısız.") from e

    if resp.status_code == 404:
        raise ValueError("Kitap bulunamadı (404).")
    if resp.status_code >= 400:
        raise ValueError(f"Open Library API hata döndü: {resp.status_code}")

    try:
        data = resp.json()
    except Exception:
        raise ValueError("Geçersiz API yanıtı: JSON parse edilemedi.")

    title = data.get("title")
    if not title:
        raise ValueError("API yanıtı geçersiz: 'title' alanı yok.")

    authors: List[str] = []
    author_refs = data.get("authors") or []
    for ref in author_refs:
        key = ref.get("key")
        if not key:
            continue
        try:
            a_resp = httpx.get(f"{base}{key}.json", timeout=10, headers=headers)
            if 300 <= a_resp.status_code < 400:
                loc = a_resp.headers.get("location") or a_resp.headers.get("Location")
                if loc:
                    a_resp = httpx.get(loc, timeout=10, headers=headers)
            if a_resp.status_code == 200:
                try:
                    a_data = a_resp.json()
                except Exception:
                    a_data = {}
                name = a_data.get("name")
                if name:
                    authors.append(name)
        except httpx.RequestError:
            continue

    if not authors:
        by_stmt = data.get("by_statement")
        if by_stmt:
            authors = [by_stmt]

    return title, authors


app = FastAPI(title="Stage-3 Library API", version="1.0.0")

storage_file = Path(__file__).with_name("library.json")
lib = Library(storage_file)
lib.load_books()


@app.get("/")
async def root():
    return {"message": "Stage-3 Library API"}


@app.get("/books", response_model=list[Book])
async def list_books(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    books = lib.list_books()
    return books[skip: skip + limit]


@app.get("/books/{isbn}", response_model=Book)
async def get_book(isbn: str = FPath(..., min_length=10)):
    book = lib.find_book(isbn)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kitap bulunamadı")
    return book


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(body: BookCreate):
    try:
        book = Book(**body.model_dump())
        lib.add_book(book)
        return book
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/books/isbn/{isbn}", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book_by_isbn(isbn: str = FPath(..., min_length=10)):
    try:
        book = lib.add_book_by_isbn(isbn)
        return book
    except ValueError as e:
        # 404 mesajını özel ele alalım
        msg = str(e)
        if "404" in msg or "bulunamadı" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@app.put("/books/{isbn}", response_model=Book)
async def update_book(isbn: str, body: BookUpdate):
    try:
        updated = lib.update_book(isbn, body)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/books/{isbn}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(isbn: str):
    try:
        lib.remove_book(isbn)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)


