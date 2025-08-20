## Python 202 Bootcamp Proje – Kütüphane Sistemi (Stage 1–3)

Modern, adım adım ilerleyen bir kütüphane projesi:
- Stage-1: OOP ile terminal tabanlı kütüphane uygulaması (kalıcı JSON depolama)
- Stage-2: Open Library API entegrasyonu ile ISBN’den otomatik ekleme (httpx)
- Stage-3: FastAPI ile REST API (CRUD ve ISBN ile ekleme)

Bu repo tüm aşamaları içerir ve her aşama bağımsız olarak çalıştırılabilir/test edilebilir.

---

## Kurulum

1) Repoyu klonlayın:
```bash
git clone <REPO_URL>
cd Python-202
```

2) Bağımlılıkları kurun:
```bash
python -m pip install -r requirements.txt
```

Alternatif olarak aşama bazlı kurulum:
```bash
# Stage-1
python -m pip install -r Stage-1/requirements.txt

# Stage-2
python -m pip install -r Stage-2/requirements.txt

# Stage-3
python -m pip install -r Stage-3/requirements.txt
```

---

## Kullanım (Usage)

### Stage-1 (Terminal Uygulaması)
```bash
python Stage-1/main.py
```
Menüden kitap ekle/sil/listele/ara işlemlerini yapabilirsiniz. Veriler `Stage-1/library.json` dosyasında kalıcıdır.

### Stage-2 (Terminal Uygulaması + Open Library)
```bash
python Stage-2/main.py
```
“ISBN ile Kitap Ekle” seçeneği Open Library API’sini kullanır ve başlık/yazar bilgilerini otomatik çeker. Gerekli bilgiler ve oran/kimlik politikaları için Open Library API dokümantasyonu: [Open Library API](https://openlibrary.org/developers/api)

### Stage-3 (FastAPI – REST API Sunucusu)

Yöntem 1 – Klasöre giderek:
```bash
cd Stage-3
uvicorn app:app --reload
```

Yöntem 2 – Proje kökünden:
```bash
python -m uvicorn Stage-3.app:app --reload
```

Sunucu çalıştığında:
- Dokümantasyon (Swagger UI): http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc

---

## API Dokümantasyonu (Stage-3)

- GET `/books`
  - Açıklama: Kitapları listeler (sayfalı)
  - Query: `skip` (varsayılan 0), `limit` (varsayılan 50)

- GET `/books/{isbn}`
  - Açıklama: ISBN’e göre tek kitap getirir

- POST `/books`
  - Açıklama: Gövdeden (body) kitap ekler
  - Body (JSON) örnek:
    ```json
    {
      "title": "Dune",
      "author": "Frank Herbert",
      "isbn": "9780441013593"
    }
    ```

- POST `/books/isbn/{isbn}`
  - Açıklama: Open Library API’den başlık/yazar bilgilerini çekerek ISBN ile kitap ekler

- PUT `/books/{isbn}`
  - Açıklama: Mevcut kitabı günceller (kısmi alanlar desteklenir)
  - Body (JSON) örnek:
    ```json
    {
      "title": "Dune (Updated)"
    }
    ```

- DELETE `/books/{isbn}`
  - Açıklama: ISBN’e göre kitabı siler

Notlar:
- Başarısız senaryolarda anlamlı hata mesajları ve uygun HTTP durum kodları döner (örn. 404 Not Found).
- Open Library sorgularında uygun `User-Agent` başlığı kullanılır. API politikaları için: [Open Library API](https://openlibrary.org/developers/api)

---

## Test Senaryoları

Her aşama için birim/sistem testleri mevcuttur. Çalıştırma örnekleri:

- Tüm Stage-1 testleri:
```bash
python -m pytest Stage-1 -q
```

- Tüm Stage-2 testleri:
```bash
python -m pytest Stage-2 -q
```

- Tüm Stage-3 testleri:
```bash
python -m pytest Stage-3 -q
```

Detaylı çıktı için `-vv` kullanabilirsiniz. Belirli bir test fonksiyonunu koşmak için `-k` ifadesi kullanılabilir.

