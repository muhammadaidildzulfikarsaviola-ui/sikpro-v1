"""Short, localized instructions for the editable quality-tool workspaces."""

QUALITY_TOOL_HELP = {
    "en": {
        "fishbone": {
            "purpose": "Organize possible causes that may contribute to a clearly stated problem. Causes are hypotheses to investigate, not proven root causes.",
            "steps": (
                "Type the problem in the Problem / effect field; it updates the diagram as you type.",
                "Choose Add cause, select a category, then enter the cause text and save it.",
                "Select a cause in the list to Edit cause, Move cause to another category, move it up or down, or Delete cause.",
                "Use Add category, Rename category, or Delete category. A category can be deleted only when it has no causes; the six built-in categories are protected.",
                "Choose PNG or PDF to export. Enter a problem statement before exporting.",
            ),
            "next": "Example: for “late deliveries,” add possible causes such as “vehicle unavailable” under the relevant category. Investigate and verify each idea with evidence. Use File → Save / Save As to save the editable .spcproj project, then File → Open Project to reopen it.",
        },
        "defect_concentration": {
            "purpose": "Record where defects appear within an inspection area so repeated locations and category patterns are easier to notice.",
            "steps": (
                "Choose Add category to create a defect type; select a category in the list before placing marks. Use Rename category to change its name.",
                "Click inside the outlined area to place a mark. Click a mark to select it; click another point inside the outline to move it.",
                "With a mark selected, choose Edit selected mark to change its category and note, or Delete selected mark to remove that mark.",
                "Use Delete category to remove a category. If it has marks, the app asks to reassign them to another category.",
                "Read each category's count in the legend and compare the mark locations to spot clusters or repeated patterns.",
                "Choose PNG or PDF to export the diagram. Use File → Save / Save As for an editable .spcproj project and File → Open Project to reopen it.",
            ),
            "next": "The outline is a simple reference area, not a selectable product shape. Imagine the inspected product or surface fitted inside it, keep the same orientation for every inspection, and place each mark at the corresponding location. For example, use the same top edge as the reference when recording scratches across several parts.",
        },
        "check_sheet": {
            "purpose": "Record inspection observations consistently and summarize the counts by category.",
            "steps": (
                "Choose Add category and enter a defect or observation type. Rename category changes its label; Delete category is available when it has no records.",
                "Choose Add record and enter the date or period, product / observation, count, notes, and category.",
                "Select a row in the table to Edit record or Delete record. Clear records removes all rows after confirmation.",
                "The summary shows the total for each category and the grand total. The bar chart uses those same entered counts.",
                "Use File → Save / Save As to save the editable .spcproj project and File → Open Project to reopen it.",
            ),
            "next": "Example: create a “Scratch” category and record a count of 3 for one inspected batch, with its date and location in Notes. Check Sheet currently has no PNG, PDF, or spreadsheet export; the records remain editable in the saved project.",
        },
    },
    "id": {
        "fishbone": {
            "purpose": "Susun kemungkinan penyebab yang dapat berkontribusi pada masalah yang dirumuskan dengan jelas. Penyebab yang dicatat adalah hipotesis untuk diselidiki, bukan akar penyebab yang sudah terbukti.",
            "steps": (
                "Ketik masalah pada kolom Masalah / akibat; diagram diperbarui saat Anda mengetik.",
                "Pilih Tambah penyebab, pilih kategori, lalu masukkan teks penyebab dan simpan.",
                "Pilih penyebab pada daftar untuk Edit penyebab, Pindahkan penyebab ke kategori lain, ubah urutannya dengan tombol atas/bawah, atau Hapus penyebab.",
                "Gunakan Tambah kategori, Ubah nama kategori, atau Hapus kategori. Kategori hanya dapat dihapus jika tidak memiliki penyebab; enam kategori bawaan dilindungi.",
                "Pilih PNG atau PDF untuk mengekspor. Isi pernyataan masalah sebelum mengekspor.",
            ),
            "next": "Contoh: untuk “pengiriman terlambat”, catat kemungkinan seperti “kendaraan tidak tersedia” pada kategori yang sesuai. Selidiki dan verifikasi setiap dugaan dengan bukti. Gunakan menu Berkas → Simpan / Simpan Sebagai untuk menyimpan proyek .spcproj yang dapat diedit, lalu Berkas → Buka Proyek untuk membukanya kembali.",
        },
        "defect_concentration": {
            "purpose": "Catat lokasi terjadinya cacat pada area pemeriksaan agar lokasi yang berulang dan pola kategori lebih mudah terlihat.",
            "steps": (
                "Pilih Tambah kategori untuk membuat jenis cacat; pilih kategori sebelum meletakkan penanda. Gunakan Ubah nama kategori untuk mengganti namanya.",
                "Klik di dalam area bergaris untuk meletakkan penanda. Klik penanda untuk memilihnya; klik titik lain di dalam batas untuk memindahkannya.",
                "Saat penanda terpilih, pilih Edit penanda terpilih untuk mengubah kategori dan catatan, atau Hapus penanda terpilih untuk menghapusnya.",
                "Gunakan Hapus kategori untuk menghapus kategori. Jika kategori memiliki penanda, aplikasi meminta Anda memindahkannya ke kategori lain.",
                "Lihat jumlah pada legenda tiap kategori dan bandingkan lokasi penanda untuk menemukan pengelompokan atau pola berulang.",
                "Pilih PNG atau PDF untuk mengekspor diagram. Gunakan Berkas → Simpan / Simpan Sebagai untuk proyek .spcproj yang dapat diedit dan Berkas → Buka Proyek untuk membukanya kembali.",
            ),
            "next": "Batas tersebut adalah area acuan sederhana, bukan bentuk produk yang dapat dipilih. Bayangkan produk atau permukaan yang diperiksa berada di dalamnya, gunakan orientasi yang sama pada setiap pemeriksaan, lalu letakkan penanda pada lokasi yang sesuai. Contoh: gunakan sisi atas yang sama sebagai acuan saat mencatat goresan pada beberapa produk.",
        },
        "check_sheet": {
            "purpose": "Catat hasil pengamatan secara konsisten dan rangkum jumlahnya berdasarkan kategori.",
            "steps": (
                "Pilih Tambah kategori lalu masukkan jenis cacat atau pengamatan. Ubah nama kategori mengganti namanya; Hapus kategori tersedia jika kategori tidak memiliki catatan.",
                "Pilih Tambah catatan lalu masukkan tanggal atau periode, produk / pengamatan, jumlah, catatan, dan kategori.",
                "Pilih baris pada tabel untuk Edit catatan atau Hapus catatan. Kosongkan catatan menghapus semua baris setelah konfirmasi.",
                "Ringkasan menampilkan jumlah tiap kategori dan jumlah total. Diagram batang menggunakan jumlah yang sama dari catatan.",
                "Gunakan Berkas → Simpan / Simpan Sebagai untuk menyimpan proyek .spcproj yang dapat diedit dan Berkas → Buka Proyek untuk membukanya kembali.",
            ),
            "next": "Contoh: buat kategori “Goresan”, lalu catat jumlah 3 untuk satu batch yang diperiksa beserta tanggal dan lokasinya pada Catatan. Lembar Periksa saat ini belum menyediakan ekspor PNG, PDF, atau spreadsheet; catatan tetap dapat diedit dari proyek yang disimpan.",
        },
    },
}
