# SPPK Final Project
**GDSS - Sistem Seleksi Beasiswa Unggulan**: 
Integrasi TOPSIS dan Borda Count dalam sistem seleksi Beasiswa Unggulan.

## Anggota Kelompok
1. Alya Putri Avianti (25/566136/PPA/07134)
2. Fayza Aulia (25/563004/PPA/07091)
3. Reni Anggraeni (25/562998/PPA/07089)
4. Nyayu Chika Marselina (25/568182/PPA/07148)

## Fitur-fitur
- Kandidat: Melakukan pendaftaran, melengkapi persyaratan, dan memantau status kelulusan.
- Admin: Melakukan verifikasi pemenuhan nilai ambang batas syarat dan validasi dokumen yang diunggah kandidat.
- Decision Maker (DM): Menghitung preferensi nilai dari para asesor menggunakan metode TOPSIS dan Borda. Pada halaman ini, terdapat asesor yang melakukan penilaian independen terhadapan kriteria substansi kandidat yang dinyatakan lolos tahap administrasi.
- Kepala Puslapdik: Menentukan kebijakan akhir yang memiliki hak untuk melakukan penggantian kandidat dengan penyesuaian peringkat secara otomatis oleh sistem.

## Cara Menjalankan
- pip install -r requirements.txt
- streamlit run app.py
