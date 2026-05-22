# generate_data.py
# Jalankan sekali: python generate_data.py

import os
import numpy as np
import pandas as pd

BASE_DIR  = 'data'
NILAI_DIR = f'{BASE_DIR}/penilaian'

for folder in [
    BASE_DIR, NILAI_DIR,
    f'{NILAI_DIR}/DM1_Esai',
    f'{NILAI_DIR}/DM2_RencanaStudi',
    f'{NILAI_DIR}/DM3_Wawancara',
]:
    os.makedirs(folder, exist_ok=True)

rng = np.random.default_rng(99)

nama_depan = [
    'Andi','Budi','Citra','Dian','Eko','Fani','Gilang','Hana','Ivan','Jeni',
    'Kiki','Lina','Mario','Nina','Oscar','Putri','Qori','Raka','Sari','Toni',
    'Umar','Vina','Wahyu','Xena','Yudi','Zahra','Adit','Bella','Candra','Dewi',
    'Elsa','Fajar','Gita','Hendra','Indah','Joko','Kartika','Lukman','Mira','Nanda',
    'Okta','Pandu','Rina','Surya','Tika','Ulfa','Vicky','Wulan','Yoga','Zulfa'
]
nama_belakang = [
    'Pratama','Santoso','Dewi','Rahayu','Nugroho','Kusuma','Arya','Putri',
    'Saputra','Lestari','Wijaya','Sari','Hidayat','Permata','Setiawan',
    'Wibowo','Arifin','Subekti','Hartono','Prabowo','Utama','Anwar',
    'Firmansyah','Amalia','Hakim','Nuraini','Siregar','Kurniawan','Maharani','Susanto'
]

batas_bahasa   = {'ITP': 550, 'PTE': 58, 'IBT': 80, 'IELTS': 6.5}
jenis_tes_list = ['ITP', 'PTE', 'IBT', 'IELTS']

rows = []
for i in range(1, 101):
    bid           = f'BU-{i:03d}'
    sedang_kuliah = bool(rng.choice([True, False], p=[0.6, 0.4]))
    batas_usia    = 33 if sedang_kuliah else 32
    usia = int(rng.integers(batas_usia+1, batas_usia+5)) if rng.random() < 0.15 \
           else int(rng.integers(21, batas_usia+1))
    ipk  = round(float(rng.uniform(2.50, 2.99)), 2) if rng.random() < 0.12 \
           else round(float(rng.uniform(3.00, 4.00)), 2)
    ukbi = int(rng.integers(500, 578)) if rng.random() < 0.10 \
           else int(rng.integers(578, 701))
    jenis_tes = str(rng.choice(jenis_tes_list))
    bmin      = batas_bahasa[jenis_tes]
    if rng.random() < 0.10:
        skor_tes = round(float(rng.uniform(4.0, 6.4)), 1) if jenis_tes == 'IELTS' \
                   else int(rng.integers(int(bmin*0.8), bmin))
    else:
        skor_tes = round(float(rng.uniform(6.5, 9.0)), 1) if jenis_tes == 'IELTS' \
                   else int(rng.integers(bmin, int(bmin*1.3)))

    def doc(mp=0.05, ip=0.03):
        r = rng.random()
        if r < mp:         return None,        False
        elif r < mp + ip:  return 'file.pdf',  False
        else:              return 'file.pdf',  True

    rek_f,  rek_v  = doc(0.05, 0.03)
    loa_f,  loa_v  = doc(0.05, 0.03)
    rs_f,   rs_v   = doc(0.04, 0.03)
    esai_f, esai_v = doc(0.04, 0.03)

    rows.append({
        'id': bid,
        'nama': f"{rng.choice(nama_depan)} {rng.choice(nama_belakang)}",
        'usia': usia, 'sedang_kuliah': sedang_kuliah,
        'ipk': ipk, 'skor_ukbi': ukbi,
        'jenis_tes_bahasa': jenis_tes, 'skor_tes_bahasa': skor_tes,
        'file_rekomendasi': rek_f,  'rekomendasi_valid': rek_v,
        'file_loa_surat_aktif': loa_f, 'loa_valid': loa_v,
        'file_rencana_studi': rs_f, 'rencana_studi_valid': rs_v,
        'file_esai': esai_f,        'esai_valid': esai_v,
    })

df = pd.DataFrame(rows)
df.to_csv(f'{BASE_DIR}/data_pendaftar.csv', index=False)
print(f'✅ data_pendaftar.csv ({len(df)} baris)')

KRITERIA_FOLDER = {
    'DM1_Esai':         ['Relevansi_Topik','Kedalaman_Analisis','Kualitas_Penulisan','Orisinalitas_Ide'],
    'DM2_RencanaStudi': ['Kejelasan_Tujuan','Kelayakan_Timeline','Relevansi_Bidang','Dampak_Rencana'],
    'DM3_Wawancara':    ['Motivasi_Komitmen','Kemampuan_Komunikasi','Pemahaman_Bidang','Leadership_Potential'],
}
for folder, kriterias in KRITERIA_FOLDER.items():
    for k in kriterias:
        nilai = rng.uniform(1, 10, (100, 10)).round(2)
        df_n  = pd.DataFrame(nilai, index=[f'BU-{i:03d}' for i in range(1,101)],
                             columns=[f'Asesor_{j+1}' for j in range(10)])
        df_n.index.name = 'id'
        df_n.to_csv(f'{NILAI_DIR}/{folder}/{k}.csv')
    print(f'✅ {folder}: {len(kriterias)} file tersimpan')

print('\n✅ Selesai! Semua data dummy ada di folder data/')