from pathlib import Path
import sys

# Test dosyasını çalıştırırken Stage-1 klasörünü sys.path'e ekle ki `import library` çalışsın
CURRENT_DIR = Path(__file__).parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from library import Book, Library


def test_book_str_format():
    book = Book("Ulysses", "James Joyce", "978-0199535675")
    assert str(book) == "Ulysses by James Joyce (ISBN: 978-0199535675)"


def test_add_and_persist(tmp_path: Path):
    store = tmp_path / "lib.json"
    lib = Library(store)
    lib.load_books()

    book = Book("Dune", "Frank Herbert", "9780441013593")
    lib.add_book(book)
    assert store.exists()

    # Yeni bir örnek ile yükle ve kontrol et
    lib2 = Library(store)
    lib2.load_books()
    found = lib2.find_book("9780441013593")
    assert found is not None
    assert found.title == "Dune"


def test_remove_book(tmp_path: Path):
    store = tmp_path / "lib.json"
    lib = Library(store)
    lib.load_books()

    book = Book("Dune", "Frank Herbert", "9780441013593")
    lib.add_book(book)

    lib.remove_book("9780441013593")
    assert lib.find_book("9780441013593") is None


def test_list_and_find(tmp_path: Path):
    store = tmp_path / "lib.json"
    lib = Library(store)
    lib.load_books()

    b1 = Book("1984", "George Orwell", "9780451524935")
    b2 = Book("The Hobbit", "J.R.R. Tolkien", "9780345339683")
    lib.add_book(b1)
    lib.add_book(b2)

    books = lib.list_books()
    assert len(books) == 2
    assert lib.find_book("9780345339683").title == "The Hobbit"


