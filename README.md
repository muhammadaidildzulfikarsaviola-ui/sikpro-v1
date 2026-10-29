# SIKPRO V1

**SIKPRO (Sistem Informasi dan Kontrol Proses)** adalah aplikasi desktop
untuk membantu mahasiswa Teknik Industri mempelajari dan menggunakan
sejumlah alat analisis kualitas serta perencanaan persediaan dalam satu
aplikasi.

> **Status proyek:** versi pengembangan. Fitur yang tercantum di bawah
> mengikuti implementasi yang telah dilaporkan. Beberapa pengujian GUI
> di luar modul Inventory belum diverifikasi ulang secara menyeluruh.

## Fitur

### Statistical Process Control (SPC)

-   Control chart: I-MR, MR, X-bar R, X-bar S, p, np, c, dan u.
-   Visualisasi histogram, Pareto, dan scatter plot.
-   Deteksi pola pelanggaran menggunakan Nelson Rules.
-   Ringkasan statistik seperti mean, UCL, dan LCL sesuai jenis chart.

### Inventory Planning

Kalkulator perencanaan persediaan, bukan sistem transaksi gudang.

-   **EOQ (Economic Order Quantity):** mode Kuantitas dan Biaya.
-   **ROP (Reorder Point):** perhitungan titik pemesanan kembali.
-   **MRP (Material Requirements Planning):** perencanaan kebutuhan
    material untuk satu item berdasarkan periode, gross requirements,
    scheduled receipts, lot-sizing, dan lead time.

### Tools pendukung

-   Histogram, Pareto, dan Scatter.
-   Fishbone diagram.
-   Check Sheet.
-   Defect Concentration Diagram.
-   Antarmuka dengan pilihan bahasa dan tema, sesuai dukungan modul.

> Daftar fitur dan nama modul dapat berubah mengikuti perkembangan versi
> aplikasi.

## Teknologi

Proyek ini menggunakan Python dan antarmuka desktop berbasis Tkinter.
Dependensi yang digunakan oleh bagian-bagian aplikasi meliputi beberapa
pustaka berikut; versi pastinya perlu mengikuti konfigurasi proyek saat
ini.

-   Python
-   Tkinter
-   Matplotlib
-   NumPy
-   Pandas
-   tksheet
-   ReportLab

## Persyaratan

-   Windows atau lingkungan lain yang mendukung Python dan Tkinter.
-   Versi Python dan dependensi sesuai konfigurasi proyek.
-   Git, jika ingin mengambil source code dari repository.

Sebelum instalasi, periksa `requirements.txt`, `pyproject.toml`, atau
berkas dependensi lain yang tersedia di repository. Gunakan berkas
konfigurasi proyek sebagai sumber versi dependensi yang paling akurat.

## Menjalankan dari source code

Clone repository:

``` bash
git clone https://github.com/muhammadaidildzulfikarsaviola-ui/sikpro-v1.git
cd sikpro-v1
```

Buat dan aktifkan virtual environment (opsional, tetapi disarankan):

``` bash
python -m venv .venv
```

Windows PowerShell:

``` powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

``` bat
.\.venv\Scripts\activate.bat
```

Instal dependensi jika repository menyediakan `requirements.txt`:

``` bash
python -m pip install -r requirements.txt
```

Jalankan entry point aplikasi sesuai struktur repository. Jika entry
point-nya `main.py`, gunakan:

``` bash
python main.py
```

> Jika nama entry point atau berkas dependensi berbeda pada checkout
> yang digunakan, ikuti instruksi dan konfigurasi aktual di repository.

## Menjalankan pengujian

Jalankan test dari root repository menggunakan runner yang dikonfigurasi
proyek. Jika proyek menggunakan `pytest`, perintah umumnya:

``` bash
python -m pytest
```

Untuk pengembangan, jalankan juga test modul yang diubah agar regresi
lebih mudah dilokalisasi.

### Catatan status pengujian

Pada verifikasi Inventory terakhir yang dilaporkan: - GUI Inventory: **6
lulus**. - Kalkulator Inventory (EOQ, ROP, MRP): **10 lulus**. -
Launcher dan navigasi: **10 lulus**. - Pengujian GUI tambahan yang
disebutkan dalam laporan tersebut lulus pada cakupan yang dijalankan.

Pengujian ini bukan klaim bahwa seluruh test suite proyek telah lulus.
Sebuah test GUI bernama `test_excel_headers_gui.py` sebelumnya mengalami
timeout ketika pengujian dijalankan. Statusnya perlu diverifikasi
kembali sebelum rilis.

## Struktur proyek

Struktur folder dapat berkembang. Beberapa bagian penting yang digunakan
dalam implementasi saat ini meliputi:

``` text
.
├── core/        # Infrastruktur bersama, termasuk bahasa dan konfigurasi
├── inventory/   # Kalkulator perencanaan persediaan
├── ui/          # Antarmuka aplikasi dan launcher
├── tests/       # Pengujian
└── main.py      # Entry point, jika tersedia pada checkout ini
```

Gunakan struktur aktual repository sebagai acuan; daftar di atas adalah
gambaran ringkas, bukan inventaris lengkap semua berkas.

## Pengembangan

Sebelum mengirim perubahan: 1. Periksa perubahan lokal dan pastikan
tidak menghapus pekerjaan yang sudah ada. 2. Jalankan test yang relevan
dengan modul yang diubah. 3. Jalankan regression test seluas mungkin. 4.
Perbarui dokumentasi jika perilaku, dependensi, atau langkah penggunaan
berubah.

## Batasan yang diketahui

-   Pengujian GUI Tkinter dapat bergantung pada lifecycle window dan
    event loop; jalankan test GUI di lingkungan yang sesuai.
-   `test_excel_headers_gui.py` pernah mengalami timeout dan belum boleh
    dianggap terselesaikan tanpa verifikasi baru.
-   Perhitungan MRP saat ini ditujukan untuk satu item sesuai
    implementasi yang dilaporkan.

## Kontribusi dan pelaporan masalah

Untuk melaporkan bug, sertakan: - langkah untuk mereproduksi masalah; -
hasil yang diharapkan dan hasil aktual; - pesan error atau traceback
jika tersedia; - versi Python dan sistem operasi; - nama modul yang
terdampak.

## Lisensi

Lisensi belum dicantumkan di README ini. Tambahkan bagian lisensi
setelah lisensi proyek ditentukan dan berkas `LICENSE` tersedia.
