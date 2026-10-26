# Laporan Audit Menyeluruh Sikpro V1

Tanggal audit: 26 Oktober 2026  
Lokasi: `D:\Code\Sikpro-v1`  
Mode: pemeriksaan dan pengujian saja; source code tidak diubah.

## A. Ringkasan Eksekutif

Aplikasi berhasil mencapai window utama `SIKPRO` dan dapat ditutup secara normal dalam lingkungan ini. Ini hanya membuktikan startup dasar; alur kerja lengkap dari input sampai ekspor belum teruji. Parser Python menerima seluruh 28 file `.py`. Kalkulator murni berhasil diimpor dan 30 pemeriksaan angka terhadap rumus independen memberi 28 lulus dan 2 gagal. Kedua kegagalan adalah batas U-chart pada ukuran sampel yang berbeda.

Terdapat bug terverifikasi pada U-chart dan Nelson Rules, serta fungsi utama yang belum tersedia: PDF, I/MR terpisah, R-bar/S-bar, fishbone, defect concentration, dan check sheet. Hasil analisis statistik selain kalkulator juga belum dibandingkan secara visual atau melalui GUI. Excel, ekspor, laporan, dan executable belum diuji end-to-end.

**Kesimpulan: BERFUNGSI SEBAGIAN.** Aplikasi start, beberapa rumus inti lulus pemeriksaan independen, tetapi ada kalkulasi yang salah dan alur/f fitur utama yang tidak tersedia atau belum terverifikasi. Belum layak dianggap andal untuk keputusan SPC.

## B. Ringkasan Pengujian

Angka di bawah menghitung skenario/asser­si numerik yang benar-benar dijalankan, bukan jumlah temuan atau fungsi yang hanya dibaca. “Belum diuji” menunjukkan alur yang disebut dalam brief namun tidak dijalankan.

| Kategori | Lulus | Gagal | Terhalang | Belum diuji |
|---|---:|---:|---:|---:|
| Startup | 1 | 0 | 0 | 12 |
| Analisis source code | 28 | 0 | 0 | 0 |
| Kalkulasi SPC | 28 | 2 | 0 | 0 |
| Nelson Rules | 3 | 5 | 0 | 0 |
| Input data | 0 | 0 | 0 | 13 |
| Impor/ekspor Excel | 0 | 0 | 0 | 13 |
| UI dan alur pengguna | 1 | 0 | 0 | 11 |
| Grafik dan quality tools | 0 | 0 | 0 | 7 |
| Laporan PDF | 0 | 1 | 0 | 8 |
| Packaging | 0 | 1 | 0 | 3 |
| Performa | 0 | 0 | 0 | 5 |

**Arti hitungan:** source code: 28 AST parse; SPC: 30 assertion nilai yang independen; Nelson: 8 pola sintetis (Rules 1–3 lulus, 4–8 gagal sesuai perilaku yang ditemukan); Startup/UI: satu smoke test window utama; PDF: satu pemeriksaan implementasi menu yang menemukan stub; Packaging: satu pemeriksaan kelengkapan manifest. Angka “belum diuji” merupakan inventaris alur yang tidak dijalankan, bukan klaim setiap variasi masukan telah dienumerasi.

## C. Temuan

### AUD-01 — P1 Tinggi — U-chart memberi batas kendali konstan untuk ukuran sampel bervariasi

- **Lokasi:** [logic/u_chart.py](D:/Code/Sikpro-v1/logic/u_chart.py:238), fungsi `calculate_u_chart`, baris 238–281; khususnya rata-rata ukuran sampel di 266–272.
- **Bukti:** untuk defects `[2,4]`, ukuran `[10,20]`, dan `u_bar=0.2`, cabang Poisson memakai `avg_n=15` lalu mengeluarkan kedua UCL `0.5464102`. Formula U-chart Poisson per observasi adalah `u_bar ± 3√(u_bar/n_i)`: UCL yang diharapkan masing-masing `0.6242641` dan `0.5000000`; LCL keduanya dipotong ke nol. Nilai aktual tidak cocok pada kedua observasi.
- **Reproduksi:** impor `calculate_u_chart`; panggil `calculate_u_chart([2,4], [10,20])`; bandingkan `ucls` dengan rumus di atas.
- **Diharapkan/aktual:** batas berubah mengikuti tiap ukuran unit; implementasi menghasilkan batas sama dari `mean(sample_sizes)`.
- **Akar/dampak:** batas memakai ukuran rata-rata, sehingga titik dapat salah diklasifikasikan sebagai terkendali/tidak terkendali saat exposure berbeda.
- **Rekomendasi:** hitung batas Poisson per `n_i`; validasi unit positif dan hitungan nonnegatif; jangan menyamakan mode distribusi yang tidak cocok dengan data u.
- **Regression test:** input di atas harus menghasilkan UCL `[0.6242640687, 0.5]`, LCL `[0,0]`, serta batas seragam ketika semua `n_i` sama.

### AUD-02 — P1 Tinggi — Nelson Rules 5 dan 6 tidak memeriksa arah yang sama

- **Lokasi:** [logic/nelson_rules.py](D:/Code/Sikpro-v1/logic/nelson_rules.py:57), baris 57–66; duplikasi antara lain di [logic/imr_chart.py](D:/Code/Sikpro-v1/logic/imr_chart.py:251) dan chart attribute/subgroup.
- **Bukti:** Rule 5 menghitung `abs(x-mean)>2σ` saja, Rule 6 menghitung `abs(x-mean)>1σ` saja. Dataset `[2.1,-2.1,0]` memicu Rule 5, dan `[1.1,-1.1,1.1,-1.1,0]` memicu Rule 6, meskipun titik yang melewati ambang berada pada sisi berlawanan. Definisi Nelson mensyaratkan sisi yang sama.
- **Reproduksi:** `check_nelson_rules(data, 0, 3, -3)` dengan dua dataset tersebut.
- **Diharapkan/aktual:** tidak ada Rules 5/6; aktual mengeluarkan pelanggaran.
- **Akar/dampak:** jumlah titik ekstrem dihitung dua sisi sekaligus; menghasilkan alarm palsu pada sinyal kualitas.
- **Rekomendasi:** hitung ambang atas dan bawah secara terpisah di setiap jendela.
- **Regression test:** kasus dua sisi di atas harus negatif; 2 dari 3 di sisi sama >2σ dan 4 dari 5 di sisi sama >1σ harus positif.

### AUD-03 — P1 Tinggi — Nelson Rule 4 memerlukan 15 titik, bukan 14

- **Lokasi:** [logic/nelson_rules.py](D:/Code/Sikpro-v1/logic/nelson_rules.py:51), baris 37–52; duplikat di `logic/imr_chart.py` baris 218–237.
- **Bukti:** implementasi menghitung perubahan arah antar-tiga titik dan menunggu `zigzag >= 13`. Untuk 14 titik bergantian terdapat 12 triple/turning point; tes `[0,1] * 7` tidak menghasilkan Rule 4. Ambang algoritma baru tercapai pada urutan 15 titik.
- **Diharapkan/aktual:** Rule 4 untuk 14 titik berturut-turut; aktual kosong.
- **Akar/dampak:** jumlah titik disamakan dengan jumlah perubahan arah tanpa koreksi indeks.
- **Rekomendasi:** hitung langsung jendela 14 observasi dan pastikan setiap pasangan berurutan bergerak berlawanan arah.
- **Regression test:** 14 titik alternating positif; 13 negatif; 15 positif dengan satu jendela pelanggaran dan indeks titik akhir yang benar.

### AUD-04 — P2 Sedang — Nelson Rule 7 mengeluarkan nilai tepat pada batas 1σ

- **Lokasi:** [logic/nelson_rules.py](D:/Code/Sikpro-v1/logic/nelson_rules.py:71), baris 68–73; duplikat di `logic/imr_chart.py` baris 284–294.
- **Bukti:** Rule 7 memakai `< zone_b`, sedangkan nilai tepat 1σ dianggap berada di dalam pita ±1σ pada definisi “within”. Dataset `[1]*15` dengan mean 0 dan sigma 1 tidak mengeluarkan Rule 7. Output berisi Rule 2 karena kesembilan titik juga satu sisi; Rule 7 tetap tidak ada.
- **Diharapkan/aktual:** Rule 7 ikut terdeteksi pada lima belas nilai tepat 1σ jika batas inklusif digunakan; aktual hanya Rule 2.
- **Rekomendasi:** tegaskan konvensi batas dan konsistenkan klasifikasi pita C pada Rule 7/8.
- **Regression test:** 15 nilai tepat ±1σ, nilai sedikit di dalam, dan sedikit di luar; periksa aturan lain secara terpisah.

### AUD-05 — P2 Sedang — Menu ekspor PDF memanggil stub dengan argumen yang salah

- **Lokasi:** [ui/ui.py](D:/Code/Sikpro-v1/ui/ui.py:67), menu memanggil `self.project_manager.generate_report` tanpa argumen; [project_managers/project_manager.py](D:/Code/Sikpro-v1/project_managers/project_manager.py:157), signature `generate_report(self, main)`.
- **Bukti:** metode membutuhkan parameter `main` tambahan, sedangkan callback menu Tk dipanggil tanpa argumen. Jika dipanggil langsung dari menu, Python menghasilkan `TypeError`. Isi metode juga hanya memanggil `withdraw`, menampilkan “Under Maintenance”, lalu `destroy`; `ProjectManager` bukan window Tk dan tidak menyediakan `withdraw`/`destroy`. `export_pdf` di baris 121 juga hanya menampilkan pesan fitur dalam pengembangan.
- **Dampak/reproduksi:** klik File → Export PDF akan gagal; tidak ada laporan PDF yang dibuat. GUI tidak diklik dalam audit, jadi TypeError dibuktikan dari signature dan callback, bukan traceback runtime.
- **Rekomendasi:** implementasikan exporter, sambungkan callback berparameter benar, dan uji file hasil tanpa menimpa file.
- **Regression test:** callback menu menghasilkan PDF valid, dapat dibuka, mencerminkan analisis aktif, dan menangani pembatalan/path error.

### AUD-06 — P2 Sedang — Dependensi runtime yang wajib tidak tercantum di requirements

- **Lokasi:** [project_managers/project_manager.py](D:/Code/Sikpro-v1/project_managers/project_manager.py:4), impor `pandas` tingkat modul; baris 99–117 untuk impor Excel; [requirements.txt](D:/Code/Sikpro-v1/requirements.txt:1) tidak memuat `pandas` maupun `openpyxl`.
- **Bukti:** `ui.ui` mengimpor `ProjectManager` saat membangun aplikasi, jadi `pandas` diperlukan untuk startup, bukan hanya saat pengguna memilih Excel. Dalam instalasi baru yang hanya memasang requirements, impor ini akan berhenti dengan `ModuleNotFoundError`; bila pandas ada tetapi openpyxl tidak, pembacaan `.xlsx` gagal. Lingkungan audit memiliki keduanya sebagai paket tambahan, sehingga runtime lokal tidak mereproduksi instalasi bersih.
- **Akar/dampak:** manifest tidak cocok dengan impor aktual; environment berbeda dapat gagal sebelum window utama.
- **Rekomendasi:** deklarasikan dan pin dependensi runtime yang dipakai, lalu verifikasi instalasi terisolasi dan build.
- **Regression test:** instalasi bersih dari manifest lalu import `main`, startup, dan baca workbook uji.

### AUD-07 — P2 Sedang — Fitur quality tool dan chart tertentu hanya placeholder/nonaktif

- **Lokasi:** [ui/ui.py](D:/Code/Sikpro-v1/ui/ui.py:105), item Fishbone, defect concentration, check sheet tanpa callback; [logic/i_chart.py](D:/Code/Sikpro-v1/logic/i_chart.py:4), `logic/mr_chart.py:5`, `logic/rbar.py:5`, `logic/sbar.py:5` menunjukkan popup “Under Maintenance”.
- **Bukti:** callback untuk tiga item menu tidak diberikan. Popup I, MR, R-bar, dan S-bar menampilkan pesan maintenance lalu ditutup. Ada kalkulator gabungan I-MR di `logic/imr_chart.py`, tetapi dua menu Individual dan Moving Range tetap tidak menjalankan fungsi.
- **Dampak:** pengguna tidak dapat menjalankan fitur yang ditampilkan sebagai menu; chart variable lengkap yang diminta tidak semuanya tersedia melalui alur aplikasi.
- **Rekomendasi:** sembunyikan/nonaktifkan menu yang belum tersedia atau implementasikan alur beserta test penerimaan.
- **Regression test:** setiap menu yang ditampilkan membuka tool yang sesuai atau secara eksplisit ditandai nonaktif.

### AUD-08 — P2 Sedang — Pembersihan data dapat merapatkan baris dan menyamarkan data tidak valid

- **Lokasi:** [ui/sheet.py](D:/Code/Sikpro-v1/ui/sheet.py:136), `get_column_data`; [logic/xbar_r.py](D:/Code/Sikpro-v1/logic/xbar_r.py:179) dan `:205`; pola sama di `logic/xbar_s.py`.
- **Bukti:** `get_column_data` membuang sel kosong; `clean_numeric` membuang nilai yang gagal dikonversi; `build_vertical_subgroups` membangun subgroup dari daftar kolom yang telah dipadatkan dan memotong ke panjang minimum. Baris yang hilang/tidak valid dapat menggeser pasangan pengukuran antar-kolom atau hilang tanpa pesan. `float('nan')` dan infinity lolos `clean_numeric`.
- **Dampak:** subgroup yang dihitung dapat memasangkan observasi dari waktu/baris berbeda dan menghasilkan hasil yang tidak merepresentasikan dataset asal.
- **Rekomendasi:** validasi per baris dengan penanda error; pertahankan indeks asli dan tolak subgroup tak lengkap/non-finite.
- **Regression test:** kolom dengan blank pada posisi berbeda, teks, NaN, dan infinity tidak boleh merapat atau menggeser pasangan; tampilkan error yang menunjuk baris.

### AUD-09 — P3 Rendah — Kasus kosong tidak ditangani konsisten oleh kalkulator

- **Lokasi:** `logic/xbar_r.py:220`, `logic/xbar_s.py:184`, `logic/p_chart.py:44`, `logic/np_chart.py:45`, `logic/c_chart.py:218`, `logic/u_chart.py:238`, `logic/imr_chart.py:117`.
- **Bukti runtime kalkulator:** Xbar-R dan Xbar-S dengan `[]` menghasilkan `IndexError`; p-chart kosong menghasilkan `ZeroDivisionError`; np-chart kosong `IndexError`; c-chart kosong mengeluarkan NaN; u-chart ukuran `[0]` menghasilkan `ZeroDivisionError`. Tidak ada satu pun yang memberi validasi domain konsisten.
- **Dampak:** input kosong/invalid dapat menimbulkan traceback atau angka NaN yang masuk ke UI/grafik.
- **Rekomendasi:** cek minimal satu subgroup/observasi sesuai chart, jumlah unit positif, finiteness, dan batas defect count sebelum kalkulasi.
- **Regression test:** kosong, satu nilai, subgroup kosong, ukuran nol, dan nilai non-finite mengeluarkan pesan validasi terkontrol tanpa menyimpan analisis.

### AUD-10 — P3 Rendah — Konflik paket pada lingkungan audit

- **Lokasi:** lingkungan Python 3.11.9; `pip check`.
- **Bukti:** `mediapipe 0.10.9` mensyaratkan `protobuf<4,>=3.11`, sedangkan environment aktif memiliki `protobuf 7.35.1`. Aplikasi tidak mengimpor mediapipe menurut pencarian source. Ini konflik environment yang teramati, bukan bukti bahwa fitur Sikpro memakainya.
- **Dampak:** paket mediapipe di environment tidak memenuhi dependensinya; risiko langsung ke Sikpro belum terbukti.
- **Rekomendasi:** jangan ubah environment audit; bersihkan manifest aplikasi dan uji dependency set terisolasi sebelum distribusi.
- **Regression test:** `pip check` pada environment hasil instalasi bersih.

## D. Hasil Verifikasi Statistik

### Control chart

Rumus pembanding mengikuti NIST/SEMATECH Engineering Statistics Handbook untuk chart variable dan attribute: [X-bar/R/S](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc321.htm), [Individuals/MR](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc312.htm), [p/np](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc332.htm), [c](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc331.htm), dan [attribute charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc33.htm). Toleransi assertion: `rel_tol=1e-9`, `abs_tol=1e-9`.

| Chart | Dataset | Rumus/konstanta & hasil yang diharapkan | Aktual | Status |
|---|---|---|---|---|
| I | `[1,2,3,2]` | CL=2; MRbar=1; σ=MRbar/1.128; UCL=4.659574468; LCL=−0.659574468 | Sama dalam toleransi | LULUS |
| MR | moving ranges `[1,1,1]` | CL=1; D3=0, D4=3.267 untuk range n=2; UCL=3.267, LCL=0 | nilai kalkulator MR chart dihitung independen; pasangan dataset di atas | LULUS |
| X-bar R | `[[1,2,3],[2,3,4]]` | n=3; A2=1.023, D3=0, D4=2.574; xbarbar=2.5, Rbar=2; X UCL/LCL=4.546/0.454; R UCL/LCL=5.148/0 | sama dalam toleransi | LULUS |
| X-bar S | dataset sama | n=3; A3=1.954, B3=0, B4=2.568; xbarbar=2.5, Sbar(sample, ddof=1)=1; X UCL/LCL=4.454/0.546; S UCL/LCL=2.568/0 | sama dalam toleransi | LULUS |
| p | subgroup defect indicator `[[1,0],[1,0,0,0]]` | pbar=2/6; UCL tiap subgroup = pbar+3√(pbar(1−pbar)/nᵢ): 1.3333333 dan 1.0404401; LCL dipotong 0 | sama | LULUS |
| np | `[[0,1,0,1],[1,0,1,0]]` | n=4; pbar=.5; npbar=2; σ=√(npbar(1−pbar))=1; UCL/LCL=5/0 | sama | LULUS |
| c | `[1,2,3]` | cbar=2; UCL/LCL=2±3√2, LCL dipotong 0 | sama: 6.242640687/0 | LULUS* |
| u | defects `[2,4]`, units `[10,20]` | ubar=.2; Poisson UCLᵢ=.2+3√(.2/nᵢ): .6242641/.5000000; LCLᵢ=0 | `.5464102/.5464102` | GAGAL |

*Rumus c-chart sesuai pendekatan 3-sigma Poisson yang digunakan, tetapi cbar=2 rendah untuk mengandalkan pendekatan normal dengan baik; interpretasi batas perlu kehati-hatian. Chart perhitungan p/np hanya diuji dalam data binary yang valid; invalid count/proportion tidak divalidasi menyeluruh. U-chart mode “Normal” dan “Binomial” tidak diverifikasi; binomial bukan model standar u-chart dan cabang Normal menggunakan SD empiris atas rate tanpa ketergantungan ukuran sampel. Hanya satu kasus numerik per chart, bukan verifikasi statistik menyeluruh untuk edge cases.

X-bar R constants n=2–10 konsisten dengan tabel NIST yang ditinjau. X-bar S constants n=2–10 dibaca dari source; nilai n=3 yang dipakai (A3=1.954, B3=0, B4=2.568) konsisten dengan konstanta standar. Batas subgroup didukung 2–10; ukuran tidak sama pada tiap subgroup tidak ditolak oleh kalkulator dan dapat membuat estimasi pooled kurang tepat. I-MR memakai MR berurutan dan d2=1.128; hanya satu dataset diperiksa. I-chart dan MR-chart terpisah pada menu merupakan placeholder.

### Nelson Rules 1–8

Referensi pola Nelson: counts 1 titik di luar 3σ; 9 satu sisi; 6 trend; 14 alternating; 2/3 >2σ pada sisi sama; 4/5 >1σ pada sisi sama; 15 dalam ±1σ; 8 tidak ada di ±1σ. Batas 2σ/1σ diperlakukan strict “lebih dari”; kasus tepat diuji khusus untuk Rule 7.

| Rule | Dataset sintetik dan ekspektasi | Aktual fungsi `logic.nelson_rules.check_nelson_rules` | Status |
|---|---|---|---|
| 1 | `[3.1]`, mean=0, UCL=3, LCL=−3 → Rule 1 | Rule 1, titik 1 | LULUS |
| 2 | sembilan nilai `[1]*9` → Rule 2 pada titik 9 | Rule 2 pada titik 9 | LULUS |
| 3 | `[1,2,3,4,5,6]` dengan batas lebar → Rule 3 pada 6 | Rule 3 pada titik 6 | LULUS |
| 4 | `[0,1]*7` (14 titik) → Rule 4 | tidak ada Rule 4 | GAGAL (off-by-one) |
| 5 | `[2.1,−2.1,0]` → negatif (sisi berbeda); companion same-side positive tidak dijalankan | Rule 5 palsu | GAGAL |
| 6 | `[1.1,−1.1,1.1,−1.1,0]` → negatif (sisi berbeda); companion same-side positive tidak dijalankan | Rule 6 palsu | GAGAL |
| 7 | `[1]*15` → pola tepat 1σ harus memenuhi “within”; Rule 2 juga wajar terjadi | Rule 2 terjadi, Rule 7 tidak | GAGAL batas |
| 8 | `[1.1,1.2,−1.1,−1.2]*2` → Rule 8; tidak ada 4/5 pada satu sisi | Rule 8 dan Rule 6 palsu | GAGAL akibat Rule 6 |

Fungsi bersama serta `imr_chart.py` memuat implementasi 1–8. Implementasi `p_chart.py`, `np_chart.py`, `c_chart.py`, `u_chart.py`, `xbar_r.py`, `xbar_s.py` berhenti setelah Rule 6 (tidak ada 4, 7, 8); fungsi chart itu juga mengulang cacat arah sama. Untuk p/u dengan batas berubah, pemeriksaan memakai rata-rata sigma pada Nelson Rules, pendekatan yang belum divalidasi sebagai skala aturan zona yang benar. Uji window overlap/index dan seluruh kasus positif, negatif, boundary untuk tiap rule belum lengkap.

## E. Bukti Runtime dan Lingkungan

- Python: `Python 3.11.9`.
- Sintaks: AST parse 28 file Python; 0 error. Ini bukan pengganti uji fungsional.
- Dependensi: paket runtime aktif dapat mengimpor kalkulator. `python -m pip check` melaporkan konflik `mediapipe 0.10.9` vs `protobuf 7.35.1` di environment ini.
- Perintah startup: `python main.py`, working directory `D:\Code\Sikpro-v1`.
- Smoke test: proses dijalankan satu kali; setelah 8 detik terlihat window utama `SIKPRO`; mengirim penutupan ke window tersebut memberi exit code 0 dan stderr kosong. Percobaan observasi awal dihentikan sebelum splash selesai dan tidak dipakai sebagai kegagalan aplikasi.
- Tidak ada traceback startup di smoke test.
- Perintah kalkulator: skrip Python inline mengimpor kalkulator dan membandingkan output ke nilai/formula independen; 30 assertion (28 lulus, 2 gagal).
- Perintah edge case: skrip Python inline memanggil kalkulator dengan input kosong dan ukuran nol; 6 variasi menghasilkan `IndexError`, `ZeroDivisionError`, atau NaN sebagaimana dirinci AUD-09.
- Perintah Nelson: skrip Python inline memanggil `logic.nelson_rules.check_nelson_rules` pada data sintetis; hasil di tabel.
- Tidak ada unit/integration test yang ditemukan dalam tree proyek.
- GUI interaktif tidak dijelajahi: tidak mengedit tksheet, menjalankan dialog Excel, memilih chart, menilai interpretasi/tampilan plot, atau mengklik menu ekspor. Jadi pembukaan window bukan verifikasi alur pengguna.
- Excel round-trip, file rusak/formula/Unicode, ekspor, PDF, installer `Installer/SetupSIKPRO_v1.0.exe`, PyInstaller build, working directory berbeda, dan pengujian performa tidak dijalankan.
- Tidak ada file pengujian atau laporan lama yang ditimpa; hanya laporan ini dibuat. Tidak ada kredensial yang ditemukan atau ditampilkan.

## F. Rencana Perbaikan

### Wajib sebelum dapat diandalkan

1. Perbaiki batas U-chart Poisson agar mengikuti ukuran sampel tiap subgroup; validasi defect/unit.
2. Perbaiki Nelson Rules 4–8 (jendela 14, arah sama pada 5/6, inklusivitas Rule 7) dan hilangkan duplikasi implementasi agar hasil antar-chart konsisten.
3. Pertahankan keterkaitan data dengan baris asal; tolak nilai kosong/non-finite/invalid secara eksplisit.
4. Lengkapi manifest dependency, lalu buktikan instalasi bersih dan startup.

### Sebaiknya dalam waktu dekat

1. Implementasikan ekspor PDF atau tandai sebagai belum tersedia dan sambungkan callback dengan benar.
2. Beri validasi input konsisten untuk seluruh kalkulator; tangani data kosong dan subgroup tidak valid tanpa traceback/NaN.
3. Beri status disabled/under-maintenance yang nyata untuk menu chart/tool yang belum berfungsi.
4. Tambahkan pengujian independen untuk semua rumus, rules, batas tepat, ukuran subgroup berubah, analisis berulang, dan round-trip Excel.

### Peningkatan opsional

1. Uji grafik dan report terhadap hasil numerik dengan verifikasi screenshot/artefak.
2. Ukur startup, dataset besar yang dibatasi, render, Excel, dan PDF; audit packaging executable dari direktori lain.
3. Tambahkan test fixture kecil yang dapat diulang dan dokumentasikan asumsi fase analisis SPC.

## G. Kesimpulan Akhir

**BERFUNGSI SEBAGIAN** — window utama Sikpro berhasil dibuka dan ditutup normal. Sejumlah rumus chart lulus uji nilai independen, tetapi U-chart dengan ukuran sampel berbeda terbukti memakai batas yang salah; Nelson Rules 4–8 memiliki kegagalan yang terbukti; PDF dan beberapa quality tools tidak berfungsi dari kode; dependency set bersih belum tervalidasi. Bukti tidak cukup untuk menyatakan workflow lengkap atau aplikasi andal.

