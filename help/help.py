HELP_DATA = {

    "en": {

        "Project": {

            "New Project": {

                "Explanation":
                """
Create a new SPC project.

This action resets current worksheet and analysis session.
                """,

                "How To Use":
                """
1. Open File menu
2. Click New Project
3. Confirm reset
4. Worksheet will be cleared automatically
5. You can also use a shortcut "Control+N" to build a new project
                """
            },

            "Open Project": {

                "Explanation":
                """
Open previously saved SPC project file.
                """,

                "How To Use":
                """
1. Open File menu
2. Click Open Project
3. Select saved project file
4. Click Open
5. You can also use a shortcut "Control+O" to open project
                """
            },

            "Save File": {

                "Explanation":
                """
Save current SPC project.
                """,

                "How To Use":
                """
1. Open File menu
2. Click Save
3. Select save location
4. Click Save
5. You can also use a shortcut "Control+S" to save project
6. You can also use a shortcut "Control+Shift+S" to save as project
                """
            }
        },

        "Data Input": {

            "Add Column": {

                "Explanation":
                """
Add worksheet column for measurement variables.
                """,

                "How To Use":
                """
1. Open Data Input menu
2. Click Add Column
3. Input column name
4. Press Enter
                """
            },

            "Edit Data": {

                "Explanation":
                """
Edit worksheet data directly from table.
                """,

                "How To Use":
                """
1. Click worksheet cell
2. Input numeric value
3. Press Enter
4. Repeat for other rows
                """
            },

            "Import Data": {

                "Explanation":
                """
Import external dataset into worksheet.
                """,

                "How To Use":
                """
1. Open File menu
2. Click Import Excel
3. Select Excel file
4. Choose worksheet if needed
5. Data will load automatically
6. You can also use a shortcut "Control+I" to import an excel data
                """
            }
        },

        "Analysis": {

            "Histogram": {

                "Explanation":
                """
Histogram analyzes data distribution.

Features:
- Simple Histogram
- Histogram With Fit
- Grouped Histogram
                """,

                "How To Use":
                """
1. Input or import numeric data
2. Open Analysis menu
3. Click Histogram
4. Select numeric column
5. Select histogram type
6. Configure bins if needed
7. Click Generate Histogram
                """,

                "Interpretation":
                """
Histogram helps identify:
- skewness
- spread
- distribution shape
- abnormal distribution
                """,

                "Common Errors":
                """
Possible errors:
- non numeric column
- empty dataset
- invalid bins value
                """
            },

            "Pareto": {

                "Explanation":
                """
Pareto chart identifies dominant defects or problems.
                """,

                "How To Use":
                """
1. Input defect/category data
2. Open Analysis menu
3. Click Pareto
4. Select defect column
5. Select frequency column if needed
6. Click Generate Pareto
                """,

                "Interpretation":
                """
Pareto helps determine:
- dominant defects
- highest frequency problems
- improvement priority
                """,

                "Common Errors":
                """
Possible errors:
- empty category column
- invalid frequency data
                """
            },

            "Scatter Plot": {

                "Explanation":
                """
Scatter plot identifies relationships between variables.
                """,

                "How To Use":
                """
1. Input numeric data
2. Open Analysis menu
3. Click Scatter Plot
4. Select X variable
5. Select Y variable
6. Configure options if needed
7. Click Generate Scatterplot
                """,

                "Interpretation":
                """
Scatterplot helps identify:
- positive correlation
- negative correlation
- weak relationship
- outliers
                """,

                "Common Errors":
                """
Possible errors:
- missing X variable
- missing Y variable
- non numeric data
                """
            }
        },

        "Control Chart": {

            "I-MR Chart": {

                "Explanation":
                """
I-MR chart is used for individual observations.

Components:
- Individual Chart
- Moving Range Chart
                """,

                "How To Use":
                """
1. Input numeric sequential data
2. Open Control Chart menu
3. Click I-MR Chart
4. Select numeric column
5. Click Generate
6. System will create:
   - I Chart
   - MR Chart
                """,

                "Interpretation":
                """
I-MR chart monitors:
- process stability
- process variation
- abnormal process behavior
                """,

                "Common Errors":
                """
Possible errors:
- empty dataset
- non numeric data
- unordered observations
                """
            },

            "Xbar-R Chart": {

                "Explanation":
                """
Xbar-R chart monitors subgroup average and range.
                """,

                "How To Use":
                """
1. Input subgroup data
2. Open Control Chart menu
3. Click Xbar-R Chart
4. Select subgroup columns
5. Configure subgroup size
6. Click Generate
                """,

                "Interpretation":
                """
Xbar-R chart monitors:
- process mean
- subgroup variation
- process consistency
                """,

                "Common Errors":
                """
Possible errors:
- inconsistent subgroup size
- empty subgroup data
- invalid numeric values
                """
            },

            "Xbar-S Chart": {

                "Explanation":
                """
Xbar-S chart monitors subgroup average and standard deviation.
                """,

                "How To Use":
                """
1. Input subgroup data
2. Open Control Chart menu
3. Click Xbar-S Chart
4. Select subgroup columns
5. Configure subgroup size
6. Click Generate
                """,

                "Interpretation":
                """
Xbar-S chart monitors:
- process average
- standard deviation
- large subgroup variation
                """,

                "Common Errors":
                """
Possible errors:
- inconsistent subgroup size
- insufficient subgroup data
                """
            },

            "p Chart": {

                "Explanation":
                """
p chart monitors defect proportion.
                """,

                "How To Use":
                """
1. Input defect proportion data
2. Open Control Chart menu
3. Click p Chart
4. Select defect column
5. Click Generate
6. System will create p Chart automatically
                """,

                "Interpretation":
                """
p chart monitors:
- defect proportion
- process stability
- quality consistency
                """,

                "Common Errors":
                """
Possible errors:
- empty dataset
- invalid proportion value
- non numeric data
                """
            },

            "np Chart": {

                "Explanation":
                """
np chart monitors defective unit count.
                """,

                "How To Use":
                """
1. Input defective unit data
2. Open Control Chart menu
3. Click np Chart
4. Select defect column
5. Click Generate
6. System will create np Chart automatically
                """,

                "Interpretation":
                """
np chart monitors:
- defective unit count
- process consistency
- changes in defect amount
                """,

                "Common Errors":
                """
Possible errors:
- inconsistent sample size
- empty dataset
- invalid numeric values
                """
            },

            "c Chart": {

                "Explanation":
                """
c chart monitors defect counts.
                """,

                "How To Use":
                """
1. Input defect count data
2. Open Control Chart menu
3. Click c Chart
4. Select defect column
5. Click Generate
6. System will create c Chart automatically
                """,

                "Interpretation":
                """
c chart monitors:
- total defects
- process quality
- defect consistency
                """,

                "Common Errors":
                """
Possible errors:
- negative defect values
- empty dataset
- non numeric data
                """
            },

            "u Chart": {

                "Explanation":
                """
u chart monitors defects per unit.
                """,

                "How To Use":
                """
1. Input defect/unit data
2. Open Control Chart menu
3. Click u Chart
4. Select required columns
5. Click Generate
6. System will create u Chart automatically
                """,

                "Interpretation":
                """
u chart monitors:
- defects per unit
- process stability
- variation between units
                """,

                "Common Errors":
                """
Possible errors:
- division by zero
- empty unit data
- invalid numeric values
                """
            }
        },

        "Export": {

            "Export PNG": {

                "Explanation":
                """
Export chart as PNG image.
                """,

                "How To Use":
                """
1. Generate chart
2. Open Export menu
3. Click Export PNG
4. Select save location
5. Save image
                """
            },

            "Export PDF": {

                "Explanation":
                """
Export analysis report as PDF.
                """,

                "How To Use":
                """
1. Generate analysis
2. Open Export menu
3. Click Export PDF
4. Select save location
5. Save PDF file
                """
            }
        },

        "System": {

            "Language": {

                "Explanation":
                """
Change application language.
                """,

                "How To Use":
                """
1. Open Language menu
2. Select language
3. Interface updates automatically
                """
            },

            "Navigator": {

                "Explanation":
                """
Navigator stores generated analysis history.
                """,

                "How To Use":
                """
1. Open Navigator panel
2. Click saved analysis item
3. Analysis will reopen automatically
                """
            }
        }
    },

    "id": {

        "Proyek": {

            "Proyek Baru": {

                "Penjelasan":
                """
Membuat proyek SPC baru.

Tindakan ini akan mereset worksheet dan analisis saat ini.
                """,

                "Cara Menggunakan":
                """
1. Buka menu File
2. Klik Proyek Baru
3. Konfirmasi reset
4. Worksheet akan dibersihkan otomatis
5. Anda juga dapat menggunakan shortcut "Control+N" untuk membuat proyek baru
                """
            },

            "Buka Proyek": {

                "Penjelasan":
                """
Membuka file proyek SPC yang telah disimpan.
                """,

                "Cara Menggunakan":
                """
1. Buka menu File
2. Klik Buka Proyek
3. Pilih file proyek
4. Klik Buka
5. Anda juga dapat menggunakan shortcut "Control+O" untuk membuka proyek
                """
            },

            "Simpan File": {

                "Penjelasan":
                """
Menyimpan proyek SPC saat ini.
                """,

                "Cara Menggunakan":
                """
1. Buka menu File
2. Klik Simpan
3. Tentukan lokasi penyimpanan
4. Klik Simpan
5. Anda juga dapat menggunakan shortcut "Control+S" untuk menyimpan proyek
6. Anda juga dapat menggunakan shortcut "Control+Shift+S" untuk menyimpan sebagai proyek baru
                """
            }
        },

        "Input Data": {

            "Tambah Kolom": {

                "Penjelasan":
                """
Menambahkan kolom worksheet baru.
                """,

                "Cara Menggunakan":
                """
1. Buka menu Input Data
2. Klik Tambah Kolom
3. Masukkan nama kolom
4. Tekan Enter
                """
            },

            "Edit Data": {

                "Penjelasan":
                """
Mengedit data worksheet langsung dari tabel.
                """,

                "Cara Menggunakan":
                """
1. Klik sel worksheet
2. Masukkan nilai numerik
3. Tekan Enter
4. Ulangi untuk baris lainnya
                """
            },

            "Impor Data": {

                "Penjelasan":
                """
Mengimpor dataset eksternal ke worksheet.
                """,

                "Cara Menggunakan":
                """
1. Buka menu File
2. Klik Impor Excel
3. Pilih file Excel
4. Pilih worksheet jika diperlukan
5. Data akan dimuat otomatis
6. Anda juga dapat menggunakan shortcut "Control+I" untuk mengimpor data Excel
                """
            }
        },

        "Analisis": {

            "Histogram": {

                "Penjelasan":
                """
Histogram digunakan untuk menganalisis distribusi data.

Fitur:
- Histogram Sederhana
- Histogram Dengan Kurva
- Histogram Grup
                """,

                "Cara Menggunakan":
                """
1. Input atau impor data numerik
2. Buka menu Analisis
3. Klik Histogram
4. Pilih kolom numerik
5. Pilih tipe histogram
6. Atur bins jika diperlukan
7. Klik Generate Histogram
                """,

                "Interpretasi":
                """
Histogram membantu mengidentifikasi:
- kemencengan distribusi
- penyebaran data
- bentuk distribusi
- distribusi abnormal
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- kolom bukan numerik
- dataset kosong
- nilai bins tidak valid
                """
            },

            "Diagram Pareto": {

                "Penjelasan":
                """
Diagram Pareto digunakan untuk mengidentifikasi masalah dominan.
                """,

                "Cara Menggunakan":
                """
1. Input data cacat/kategori
2. Buka menu Analisis
3. Klik Diagram Pareto
4. Pilih kolom cacat
5. Pilih kolom frekuensi jika diperlukan
6. Klik Generate Pareto
                """,

                "Interpretasi":
                """
Diagram Pareto membantu menentukan:
- cacat dominan
- masalah dengan frekuensi tertinggi
- prioritas perbaikan
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- kolom kategori kosong
- data frekuensi tidak valid
                """
            },

            "Scatter Plot": {

                "Penjelasan":
                """
Scatter plot digunakan untuk menganalisis hubungan antar variabel.
                """,

                "Cara Menggunakan":
                """
1. Input data numerik
2. Buka menu Analisis
3. Klik Scatter Plot
4. Pilih variabel X
5. Pilih variabel Y
6. Atur opsi jika diperlukan
7. Klik Generate Scatterplot
                """,

                "Interpretasi":
                """
Scatter plot membantu mengidentifikasi:
- korelasi positif
- korelasi negatif
- hubungan lemah
- outlier
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- variabel X kosong
- variabel Y kosong
- data bukan numerik
                """
            }
        },

        "Peta Kendali": {

            "Peta I-MR": {

                "Penjelasan":
                """
Peta I-MR digunakan untuk observasi individual.

Komponen:
- Peta Individual
- Peta Moving Range
                """,

                "Cara Menggunakan":
                """
1. Input data numerik berurutan
2. Buka menu Peta Kendali
3. Klik Peta I-MR
4. Pilih kolom numerik
5. Klik Generate
6. Sistem akan membuat:
   - Peta I
   - Peta MR
                """,

                "Interpretasi":
                """
Peta I-MR digunakan untuk memantau:
- kestabilan proses
- variasi proses
- perilaku proses abnormal
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- dataset kosong
- data bukan numerik
- observasi tidak berurutan
                """
            },

            "Peta Xbar-R": {

                "Penjelasan":
                """
Peta Xbar-R digunakan untuk memantau rata-rata dan range subgroup.
                """,

                "Cara Menggunakan":
                """
1. Input data subgroup
2. Buka menu Peta Kendali
3. Klik Peta Xbar-R
4. Pilih kolom subgroup
5. Atur ukuran subgroup
6. Klik Generate
                """,

                "Interpretasi":
                """
Peta Xbar-R digunakan untuk memantau:
- rata-rata proses
- variasi subgroup
- konsistensi proses
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- ukuran subgroup tidak konsisten
- data subgroup kosong
- nilai numerik tidak valid
                """
            },

            "Peta Xbar-S": {

                "Penjelasan":
                """
Peta Xbar-S digunakan untuk memantau rata-rata dan standar deviasi subgroup.
                """,

                "Cara Menggunakan":
                """
1. Input data subgroup
2. Buka menu Peta Kendali
3. Klik Peta Xbar-S
4. Pilih kolom subgroup
5. Atur ukuran subgroup
6. Klik Generate
                """,

                "Interpretasi":
                """
Peta Xbar-S digunakan untuk memantau:
- rata-rata proses
- standar deviasi
- variasi subgroup besar
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- ukuran subgroup tidak konsisten
- data subgroup tidak mencukupi
                """
            },

            "Peta p": {

                "Penjelasan":
                """
Peta p digunakan untuk memantau proporsi produk cacat.
                """,

                "Cara Menggunakan":
                """
1. Input data proporsi cacat
2. Buka menu Peta Kendali
3. Klik Peta p
4. Pilih kolom cacat
5. Klik Generate
6. Sistem akan membuat grafik p Chart otomatis
                """,

                "Interpretasi":
                """
Peta p membantu memantau:
- proporsi cacat proses
- kestabilan kualitas
- perubahan tingkat kecacatan
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- data kosong
- nilai proporsi tidak valid
- kolom bukan numerik
                """
            },

            "Peta np": {

                "Penjelasan":
                """
Peta np digunakan untuk memantau jumlah unit cacat.
                """,

                "Cara Menggunakan":
                """
1. Input data jumlah unit cacat
2. Buka menu Peta Kendali
3. Klik Peta np
4. Pilih kolom cacat
5. Klik Generate
6. Sistem akan membuat grafik np Chart otomatis
                """,

                "Interpretasi":
                """
Peta np membantu memantau:
- jumlah produk cacat
- kestabilan proses produksi
- perubahan jumlah cacat
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- dataset kosong
- ukuran sampel tidak konsisten
- data bukan numerik
                """
            },

            "Peta c": {

                "Penjelasan":
                """
Peta c digunakan untuk memantau jumlah cacat dalam suatu unit inspeksi.
                """,

                "Cara Menggunakan":
                """
1. Input data jumlah cacat
2. Buka menu Peta Kendali
3. Klik Peta c
4. Pilih kolom jumlah cacat
5. Klik Generate
6. Sistem akan membuat grafik c Chart otomatis
                """,

                "Interpretasi":
                """
Peta c membantu memantau:
- jumlah cacat proses
- kestabilan kualitas
- variasi jumlah defect
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- data kosong
- nilai cacat negatif
- kolom bukan numerik
                """
            },

            "Peta u": {

                "Penjelasan":
                """
Peta u digunakan untuk memantau jumlah cacat per unit.
                """,

                "Cara Menggunakan":
                """
1. Input data jumlah cacat dan jumlah unit
2. Buka menu Peta Kendali
3. Klik Peta u
4. Pilih kolom yang dibutuhkan
5. Klik Generate
6. Sistem akan membuat grafik u Chart otomatis
                """,

                "Interpretasi":
                """
Peta u membantu memantau:
- cacat per unit
- kestabilan proses
- variasi defect antar unit
                """,

                "Kemungkinan Galat":
                """
Kemungkinan error:
- data unit kosong
- pembagian dengan nol
- data bukan numerik
                """
            }
        },

        "Ekspor": {

            "Ekspor PNG": {

                "Penjelasan":
                """
Mengekspor chart sebagai gambar PNG.
                """,

                "Cara Menggunakan":
                """
1. Generate chart
2. Buka menu Ekspor
3. Klik Ekspor PNG
4. Pilih lokasi penyimpanan
5. Simpan gambar
                """
            },

            "Ekspor PDF": {

                "Penjelasan":
                """
Mengekspor laporan analisis sebagai PDF.
                """,

                "Cara Menggunakan":
                """
1. Generate analisis
2. Buka menu Ekspor
3. Klik Ekspor PDF
4. Pilih lokasi penyimpanan
5. Simpan file PDF
                """
            }
        },

        "Sistem": {

            "Bahasa": {

                "Penjelasan":
                """
Mengubah bahasa aplikasi.
                """,

                "Cara Menggunakan":
                """
1. Buka menu Bahasa
2. Pilih bahasa
3. Tampilan akan berubah otomatis
                """
            },

            "Navigator": {

                "Penjelasan":
                """
Navigator menyimpan riwayat analisis yang telah dibuat.
                """,

                "Cara Menggunakan":
                """
1. Buka panel Navigator
2. Klik item analisis
3. Analisis akan dibuka kembali otomatis
                """
            }
        }
    }
}