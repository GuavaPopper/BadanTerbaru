import sqlite3
import pandas as pd
from tabulate import tabulate
import os

def connect_db():
    db_path = 'measurements.db'
    if not os.path.exists(db_path):
        print("Database belum ada. Silakan lakukan pengukuran terlebih dahulu.")
        return None
    return sqlite3.connect(db_path)

def view_all_measurements():
    conn = connect_db()
    if conn is None:
        return
    
    try:
        # Membaca data menggunakan pandas
        query = "SELECT * FROM measurements ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("\nBelum ada data pengukuran dalam database.")
        else:
            print("\nData Pengukuran:")
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Menampilkan statistik dasar
            print("\nStatistik Pengukuran:")
            stats = df[['height', 'shoulder_width', 'chest_circumference', 'waist_circumference']].describe()
            print(tabulate(stats, headers='keys', tablefmt='psql', floatfmt='.2f'))
    
    except sqlite3.Error as e:
        print(f"Error saat membaca database: {e}")
    
    finally:
        conn.close()

def export_to_csv():
    conn = connect_db()
    if conn is None:
        return
    
    try:
        df = pd.read_sql_query("SELECT * FROM measurements", conn)
        if not df.empty:
            filename = 'measurement_history.csv'
            df.to_csv(filename, index=False)
            print(f"\nData berhasil diekspor ke {filename}")
        else:
            print("\nTidak ada data untuk diekspor")
    
    except sqlite3.Error as e:
        print(f"Error saat mengekspor data: {e}")
    
    finally:
        conn.close()

def delete_measurement(measurement_id):
    conn = connect_db()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"\nPengukuran dengan ID {measurement_id} berhasil dihapus")
        else:
            print(f"\nTidak ditemukan pengukuran dengan ID {measurement_id}")
    
    except sqlite3.Error as e:
        print(f"Error saat menghapus data: {e}")
    
    finally:
        conn.close()

def main():
    while True:
        print("\nMenu Pengukuran Badan:")
        print("1. Lihat semua data pengukuran")
        print("2. Export data ke CSV")
        print("3. Hapus data pengukuran")
        print("4. Keluar")
        
        choice = input("\nPilih menu (1-4): ")
        
        if choice == '1':
            view_all_measurements()
        
        elif choice == '2':
            export_to_csv()
        
        elif choice == '3':
            measurement_id = input("Masukkan ID pengukuran yang akan dihapus: ")
            if measurement_id.isdigit():
                delete_measurement(int(measurement_id))
            else:
                print("ID tidak valid")
        
        elif choice == '4':
            print("\nTerima kasih telah menggunakan aplikasi!")
            break
        
        else:
            print("\nPilihan tidak valid")

if __name__ == "__main__":
    main() 