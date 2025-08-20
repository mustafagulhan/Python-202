from pathlib import Path
from library import Library


def prompt(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except EOFError:
        return ""


def main() -> None:
    storage = Path(__file__).with_name("library.json")
    lib = Library(storage)
    lib.load_books()

    menu = (
        "\n=== Kütüphane Uygulaması (Stage-2) ===\n"
        "1) ISBN ile Kitap Ekle (Open Library)\n"
        "2) Kitap Sil\n"
        "3) Kitapları Listele\n"
        "4) Kitap Ara\n"
        "5) Çıkış\n"
    )

    while True:
        print(menu)
        choice = prompt("Seçiminiz: ").strip()

        if choice == "1":
            isbn = prompt("ISBN: ").strip()
            try:
                book = lib.add_book_by_isbn(isbn)
                print(f"Eklendi: {book}")
            except ValueError as e:
                print(f"Hata: {e}")

        elif choice == "2":
            isbn = prompt("Silinecek kitabın ISBN'i: ").strip()
            try:
                lib.remove_book(isbn)
                print("Kitap silindi.")
            except ValueError as e:
                print(f"Hata: {e}")

        elif choice == "3":
            books = lib.list_books()
            if not books:
                print("Kütüphanede kitap yok.")
            else:
                for idx, b in enumerate(books, start=1):
                    print(f"{idx}. {b}")

        elif choice == "4":
            isbn = prompt("Aranacak ISBN: ").strip()
            book = lib.find_book(isbn)
            if book:
                print(book)
            else:
                print("Kitap bulunamadı.")

        elif choice == "5":
            print("Güle güle!")
            break

        else:
            print("Geçersiz seçim. Lütfen 1-5 arasında bir değer girin.")


if __name__ == "__main__":
    main()
