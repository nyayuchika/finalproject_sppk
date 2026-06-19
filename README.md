# SPPK Final Project - Kelompok 2
**GDSS - Sistem Seleksi Beasiswa Unggulan**: 
Integrasi TOPSIS dan Borda Count dalam sistem seleksi Beasiswa Unggulan.

## Anggota Kelompok
1. Alya Putri Avianti (25/566136/PPA/07134)
2. Fayza Aulia (25/563004/PPA/07091)
3. Reni Anggraeni (25/562998/PPA/07089)
4. Nyayu Chika Marselina (25/568182/PPA/07148)

## Cara Menjalankan
- Clone repositori _finalproject_sppk_ terlebih dahulu
- Jalankan pip install -r requirements.txt pada CMD
- Jalankan streamlit run app.py pada CMD
- Halaman awal akan dijalankan pada localhost:8501

## Pages yang ada pada sistem
- **Halaman Awal**: Kandidat baru mendaftar akun dan melakukan login. Khusus panitia seleksi Beasiswa Unggulan, seperti admin, decision maker, dan Kepala Puslapdik diasumsikan sudah memiliki akun dan dapat langsung login.
- **Halaman Kandidat**: Kandidat mengisi data diri  serta melengkapi dan mengunggah dokumen persyaratan, seperti esai, rencana studi, Letter of Acceptance (LoA), dan surat rekomendasi.
- **Halaman Admin**: Sistem melakukan pengecekan otomatis pada nilai IPK, TOEFL, UKBI, dan lain sebagainya yang menjadi persyaratan. Jika kandidat lolos verifikasi administrasi, maka panitia tahap administrasi akan melakukan verifikasi keabsahan dokumen yang diunggah kandidat.
- **Halaman Decision Maker (DM)**: 10 asesor per kriteria menilai berkas secara paralel sesuai dengan subkriteria, yaitu esai, rencana studi, dan wawancara.
- **Halaman Kepala Puslapdik**: Kepala Puslapdik meninjau ranking final. Jika ada kandidat yang diganti, sistem akan melakukan auto-rerank dimana peserta di bawahnya otomatis naik mengisi kuota yang masih tersisa. Sistem backend menghitung nilai setiap subkriteria menggunakan TOPSIS per DM lalu dikumulatifkan menggunakan Borda Count. Perhitungan yang dilakukan menggunakan TOPSIS dan Borda Count tidak ditampilkan pada halaman user-interface, hanya dilakukan pada backend.
