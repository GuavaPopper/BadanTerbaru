# Migrasi Database ke Supabase

Dokumentasi ini berisi langkah-langkah untuk migrasi database SQLite ke Supabase untuk aplikasi Body Measurement System.

## Apa yang telah dilakukan

1. Database SQLite telah berhasil dimigrasi ke Supabase
2. Table `measurements` telah dibuat di Supabase dengan struktur yang sama dengan tabel di SQLite
3. Semua data pengukuran telah dipindahkan ke Supabase
4. File koneksi ke Supabase telah dibuat (`backend/src/supabase_connection.py`)
5. Contoh aplikasi Flask yang menggunakan Supabase telah dibuat (`backend/src/app_supabase.py`)

## Cara Menggunakan

### 1. Installasi Library

Tambahkan library Supabase ke dalam `requirements.txt`:

```
supabase>=2.0.0
```

Lalu install dengan perintah:

```
pip install -r requirements.txt
```

### 2. Konfigurasi Environment

Pastikan file `.env` di direktori utama (root) aplikasi berisi konfigurasi Supabase berikut:

```
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Email Configuration (sesuaikan dengan konfigurasi Anda)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SECRET_KEY=your-secret-key
```

**CATATAN PENTING**: Jangan pernah menyertakan file `.env` yang berisi kredensial asli ke dalam repository Git. Gunakan `.env.example` sebagai template saja.

### 3. Menggunakan Supabase

File `supabase_connection.py` berisi fungsi-fungsi untuk mengakses database Supabase:

- `get_all_measurements()` - Mendapatkan semua data pengukuran
- `get_latest_measurement()` - Mendapatkan data pengukuran terbaru
- `insert_measurement(data)` - Menambahkan data pengukuran baru

Contoh penggunaan:

```python
from supabase_connection import get_all_measurements, get_latest_measurement, insert_measurement

# Mendapatkan semua pengukuran
measurements = get_all_measurements()

# Mendapatkan pengukuran terbaru
latest = get_latest_measurement()

# Menambahkan pengukuran baru
new_data = {
    "height": 175.0,
    "shoulder_width": 45.0,
    "chest_circumference": 95.0,
    "waist_circumference": 80.0
}
result = insert_measurement(new_data)
```

### 4. Menjalankan Aplikasi dengan Supabase

Untuk menjalankan aplikasi dengan Supabase, gunakan file `app_supabase.py`:

```
cd backend/src
python app_supabase.py
```

## Mengakses Dashboard Supabase

URL: https://app.supabase.com
Project: BodyMeasurementsDB

Anda dapat mengakses dashboard Supabase untuk melihat data dan melakukan perubahan lainnya seperti menambahkan tabel baru, mengubah struktur tabel, dll. 