# Data pengukuran
manual_measurements = {
    'Tinggi Badan': 180,
    'Lebar Bahu': 47,
    'Lingkar Dada': 120,
    'Lingkar Pinggang': 114
}

system_measurements = {
    'Tinggi Badan': 178,
    'Lebar Bahu': 59,
    'Lingkar Dada': 137,
    'Lingkar Pinggang': 136
}

# Menghitung error
error_values = {}
error_percentage = {}
accuracy_values = {}

for key in manual_measurements:
    error_values[key] = abs(system_measurements[key] - manual_measurements[key])
    error_percentage[key] = round(error_values[key] / manual_measurements[key] * 100, 1)
    accuracy_values[key] = round(100 - error_percentage[key], 1)

# Hitung rata-rata
avg_error = sum(error_percentage.values()) / len(error_percentage)
avg_accuracy = 100 - avg_error

# Membuat format tabel
def format_table(headers, data):
    # Menentukan lebar kolom
    col_width = [max(len(str(row[i])) for row in data + [headers]) + 2 for i in range(len(headers))]
    
    # Membuat garis pemisah
    separator = '+' + '+'.join('-' * width for width in col_width) + '+'
    
    # Membuat header
    result = [separator]
    header_row = '|' + '|'.join(str(headers[i]).center(col_width[i]) for i in range(len(headers))) + '|'
    result.append(header_row)
    result.append(separator)
    
    # Membuat baris data
    for row in data:
        data_row = '|' + '|'.join(str(row[i]).center(col_width[i]) for i in range(len(row))) + '|'
        result.append(data_row)
    
    result.append(separator)
    return '\n'.join(result)

# Menyiapkan data untuk tabel
headers = ['Parameter', 'Manual (cm)', 'Sistem (cm)', 'Error (cm)', 'Error (%)', 'Akurasi (%)']
table_data = []

for key in manual_measurements:
    row = [
        key, 
        manual_measurements[key], 
        system_measurements[key], 
        error_values[key], 
        f"{error_percentage[key]}%", 
        f"{accuracy_values[key]}%"
    ]
    table_data.append(row)

# Menambahkan rata-rata
table_data.append([
    'Rata-rata', 
    '-', 
    '-', 
    '-', 
    f"{avg_error:.1f}%", 
    f"{avg_accuracy:.1f}%"
])

# Tampilkan hasil
print("\n==== PERBANDINGAN PENGUKURAN MANUAL VS SISTEM ====\n")
print(format_table(headers, table_data))

# Simpan hasil ke file
with open('measurement_comparison_results.txt', 'w') as f:
    f.write("==== PERBANDINGAN PENGUKURAN MANUAL VS SISTEM ====\n\n")
    f.write(format_table(headers, table_data))
    f.write("\n\nHasil ini dapat digunakan untuk bagian 5.3 Kinerja/Performansi beserta Evaluasi pada proposal")

print("\nHasil perbandingan telah disimpan dalam file 'measurement_comparison_results.txt'")

# Visualisasi data menggunakan matplotlib
try:
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Membuat figure dengan ukuran yang sesuai
    plt.figure(figsize=(14, 10))
    
    # 1. Visualisasi perbandingan pengukuran manual vs sistem
    plt.subplot(2, 1, 1)
    parameters = list(manual_measurements.keys())
    x = np.arange(len(parameters))
    width = 0.35
    
    # Membuat bar chart
    plt.bar(x - width/2, list(manual_measurements.values()), width, label='Pengukuran Manual', color='#3498db')
    plt.bar(x + width/2, list(system_measurements.values()), width, label='Pengukuran Sistem', color='#e74c3c')
    
    # Menambahkan label dan title
    plt.xlabel('Parameter Pengukuran', fontsize=12)
    plt.ylabel('Nilai (cm)', fontsize=12)
    plt.title('Perbandingan Pengukuran Manual vs Sistem', fontsize=14, fontweight='bold')
    plt.xticks(x, parameters, fontsize=10)
    plt.legend(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Menambahkan nilai di atas bar
    for i, v in enumerate(manual_measurements.values()):
        plt.text(i - width/2, v + 3, str(v), ha='center', fontsize=9)
    for i, v in enumerate(system_measurements.values()):
        plt.text(i + width/2, v + 3, str(v), ha='center', fontsize=9)
    
    # 2. Visualisasi error dan akurasi
    plt.subplot(2, 1, 2)
    
    # Membuat bar chart untuk error dan akurasi
    plt.bar(x - width/2, list(error_percentage.values()), width, label='Error (%)', color='#e74c3c')
    plt.bar(x + width/2, list(accuracy_values.values()), width, label='Akurasi (%)', color='#2ecc71')
    
    # Menambahkan label dan title
    plt.xlabel('Parameter Pengukuran', fontsize=12)
    plt.ylabel('Persentase (%)', fontsize=12)
    plt.title('Error dan Akurasi Pengukuran', fontsize=14, fontweight='bold')
    plt.xticks(x, parameters, fontsize=10)
    plt.legend(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Menambahkan nilai di atas bar
    for i, v in enumerate(error_percentage.values()):
        plt.text(i - width/2, v + 3, f"{v}%", ha='center', fontsize=9)
    for i, v in enumerate(accuracy_values.values()):
        plt.text(i + width/2, v + 3, f"{v}%", ha='center', fontsize=9)
    
    # Menambahkan garis untuk rata-rata
    plt.axhline(y=avg_error, color='#e74c3c', linestyle='--', alpha=0.7)
    plt.text(len(parameters)-1, avg_error + 3, f"Rata-rata Error: {avg_error:.1f}%", ha='right', color='#e74c3c')
    
    plt.axhline(y=avg_accuracy, color='#2ecc71', linestyle='--', alpha=0.7)
    plt.text(len(parameters)-1, avg_accuracy + 3, f"Rata-rata Akurasi: {avg_accuracy:.1f}%", ha='right', color='#2ecc71')
    
    # Mengatur layout dan menyimpan gambar
    plt.tight_layout()
    plt.savefig('measurement_comparison.png', dpi=300, bbox_inches='tight')
    
    print("Visualisasi telah disimpan dalam file 'measurement_comparison.png'")
except ImportError:
    print("\nUntuk membuat visualisasi, install matplotlib dengan perintah:")
    print("pip install matplotlib")
    print("Kemudian jalankan script ini kembali.") 