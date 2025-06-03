# Sistem Pengukuran Dimensi Tubuh

Aplikasi pengukuran dimensi tubuh menggunakan computer vision dan MediaPipe untuk mengukur tinggi badan, lebar bahu, lingkar dada, dan lingkar pinggang secara real-time.

## Fitur Utama
- 🎯 Deteksi jarak wajah untuk kalibrasi
- 📏 Pengukuran tinggi badan
- 👕 Pengukuran lebar bahu
- 🔄 Estimasi lingkar dada
- ⭕ Estimasi lingkar pinggang
- 🎥 Real-time video processing
- 📊 Visualisasi hasil pengukuran
- 🔊 Panduan suara

## Persyaratan Sistem
- Python 3.7 atau lebih baru
- Webcam
- Sistem Operasi: Windows/Linux/MacOS

## Instalasi

1. Clone repository ini:
```bash
git clone [URL_REPOSITORY]
cd Height-Detection-main
```

2. Buat dan aktifkan virtual environment:
```bash
# Membuat virtual environment
python -m venv venv

# Mengaktifkan virtual environment
# Untuk Windows:
venv\Scripts\activate
# Untuk Linux/Mac:
source venv/bin/activate
```

3. Install dependencies yang diperlukan:
```bash
pip install -r requirements.txt
```

4. Deaktivasi virtual environment setelah selesai:
```bash
deactivate
```

## Cara Penggunaan

1. Jalankan aplikasi:
```bash
python backend/src/app.py
```

2. Buka browser dan akses:
```
http://127.0.0.1:5000
```

### Mode Face Detection
1. Pada halaman awal, sistem akan mengaktifkan mode deteksi wajah
2. Posisikan wajah Anda di depan kamera
3. Perhatikan indikator jarak:
   - Warna hijau: jarak ideal (330-360 cm)
   - Teks akan menampilkan "Perfect distance for measurement!" saat posisi tepat
4. Klik tombol "Lakukan Ukur Badan" untuk melanjutkan ke pengukuran tubuh

### Mode Body Detection
1. Berdiri tegak menghadap kamera dengan jarak yang sudah dikalibrasi
2. Pastikan seluruh tubuh terlihat dalam frame
3. Sistem akan menampilkan:
   - Tinggi badan (dalam cm)
   - Lebar bahu (dalam cm)
   - Estimasi lingkar dada (dalam cm)
   - Estimasi lingkar pinggang (dalam cm)
4. Untuk hasil terbaik:
   - Gunakan pakaian yang pas (tidak terlalu longgar)
   - Berdiri dengan postur tegak
   - Pastikan pencahayaan cukup
   - Hindari gerakan berlebihan

### Navigasi Antar Mode
- Klik "Return to Face Detection" untuk kembali ke mode kalibrasi jarak
- Klik "Lakukan Ukur Badan" untuk beralih ke mode pengukuran tubuh

## Struktur Folder
```
Height-Detection-main/
├── backend/
│   ├── src/                    # Source code
│   ├── models/                 # Model ML
│   ├── utils/                  # Fungsi utilitas
│   ├── config/                 # File konfigurasi
│   └── assets/                 # Media
├── templates/                  # Template HTML
├── static/                    # File statis (CSS, JS)
├── requirements.txt           # Dependencies
└── README.md                 # Dokumentasi
```

## Troubleshooting

### Kamera Tidak Terdeteksi
- Pastikan tidak ada aplikasi lain yang menggunakan kamera
- Periksa izin kamera di sistem operasi
- Restart aplikasi

### Pengukuran Tidak Akurat
- Pastikan jarak sudah dikalibrasi dengan benar
- Gunakan pencahayaan yang cukup
- Hindari background yang terlalu ramai
- Pastikan postur tubuh tegak dan stabil

### Aplikasi Tidak Berjalan
- Periksa instalasi Python dan dependencies
- Pastikan port 5000 tidak digunakan aplikasi lain
- Periksa log error di terminal
