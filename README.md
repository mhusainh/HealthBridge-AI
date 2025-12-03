# HealthBridge-AI 🏥

HealthBridge-AI adalah sistem cerdas yang dirancang untuk membantu tenaga medis dalam menganalisis rekam medis pasien (format FHIR). Sistem ini menggunakan **Google Gemini AI** untuk mendeteksi potensi bahaya seperti interaksi obat, kontraindikasi alergi, dan duplikasi resep, serta memvisualisasikan hubungan data medis dalam bentuk **Knowledge Graph**.

## 📂 Struktur Proyek

- **`AI/`**: Folder utama aplikasi.
  - `app.py`: Aplikasi Frontend berbasis **Streamlit** (Dashboard Interaktif).
  - `main.py`: Aplikasi Backend API berbasis **FastAPI**.
  - `ai_service.py`: Modul logika utama untuk pemrosesan data dan integrasi AI.
  - `ai_logic.ipynb`: Notebook untuk eksperimen dan prototyping logika AI.
- **`generate_dataset.py`**: Script untuk membuat dataset dummy (FHIR JSON).
- **`fhir_data_1000.json`**: Contoh dataset rekam medis pasien.

## ⚙️ Persiapan (Installation)

1.  **Clone Repository**

    ```bash
    git clone https://github.com/mhusainh/HealthBridge-AI.git
    cd HealthBridge-AI
    ```

2.  **Install Dependencies**
    Pastikan Python sudah terinstal, lalu jalankan perintah berikut untuk menginstal library yang dibutuhkan:

    ```bash
    pip install streamlit fastapi uvicorn google-generativeai networkx matplotlib python-dotenv requests
    ```

3.  **Konfigurasi Environment (.env)**
    Buat file `.env` di dalam folder `AI/` dan isi dengan konfigurasi berikut:
    ```ini
    GOOGLE_API_KEY="MASUKKAN_API_KEY_GEMINI_ANDA_DISINI"
    FILENAME="../fhir_data_1000.json"
    ```
    > **Catatan:** `FILENAME` mengarah ke file dataset JSON. Jika file ada di folder root (satu level di atas folder AI), gunakan `../nama_file.json`.

## 🚀 Cara Menjalankan Aplikasi

Anda memiliki dua opsi untuk menjalankan aplikasi ini: sebagai Dashboard Web (Streamlit) atau sebagai API Server (FastAPI).

### Opsi 1: Menjalankan Dashboard Web (Streamlit)

Gunakan opsi ini jika Anda ingin tampilan visual interaktif untuk memilih pasien, melihat graf, dan hasil analisis AI.

1.  Buka terminal dan masuk ke folder `AI`:
    ```bash
    cd AI
    ```
2.  Jalankan perintah:
    ```bash
    streamlit run app.py
    ```
3.  Browser akan otomatis terbuka di alamat `http://localhost:8501`.

### Opsi 2: Menjalankan Backend API (FastAPI)

Gunakan opsi ini jika Anda ingin menyediakan layanan API untuk aplikasi lain (misalnya Frontend React/Mobile).

1.  Buka terminal dan masuk ke folder `AI`:
    ```bash
    cd AI
    ```
2.  Jalankan perintah:
    ```bash
    python main.py
    ```
    _Atau menggunakan uvicorn langsung:_
    ```bash
    uvicorn main:app --reload
    ```
3.  Server akan berjalan di `http://localhost:8000`.
4.  Anda bisa mengakses dokumentasi API (Swagger UI) di `http://localhost:8000/docs`.

## 🛠️ Troubleshooting

- **File JSON Tidak Ditemukan**:
  Pastikan file `fhir_data_1000.json` ada di folder root proyek. Jika belum ada, jalankan script generator:

  ```bash
  python generate_dataset.py
  ```

  Lalu pastikan path di `.env` sudah benar (`../fhir_data_1000.json` jika menjalankan dari folder `AI`).

- **Error API Key**:
  Pastikan Anda sudah memiliki API Key dari Google AI Studio dan memasukkannya ke dalam file `.env` dengan nama variabel `GOOGLE_API_KEY`.
