# spk_engine.py

import numpy as np
import pandas as pd

BASE_DIR  = 'data'
NILAI_DIR = f'{BASE_DIR}/penilaian'

BATAS_BAHASA      = {'ITP': 550, 'PTE': 58, 'IBT': 80, 'IELTS': 6.5}
BATAS_IPK         = 3.00
BATAS_UKBI        = 578
BATAS_USIA_UMUM   = 32
BATAS_USIA_KULIAH = 33

KRITERIA = {
    'DM1_Esai': {
        'label': 'DM 1 — Esai',
        'folder': 'DM1_Esai',
        'kriteria': [
            {'nama': 'Relevansi_Topik',       'bobot': 0.25, 'tipe': 'benefit'},
            {'nama': 'Kedalaman_Analisis',     'bobot': 0.30, 'tipe': 'benefit'},
            {'nama': 'Kualitas_Penulisan',     'bobot': 0.25, 'tipe': 'benefit'},
            {'nama': 'Orisinalitas_Ide',       'bobot': 0.20, 'tipe': 'benefit'},
        ]
    },
    'DM2_RencanaStudi': {
        'label': 'DM 2 — Rencana Studi',
        'folder': 'DM2_RencanaStudi',
        'kriteria': [
            {'nama': 'Kejelasan_Tujuan',       'bobot': 0.30, 'tipe': 'benefit'},
            {'nama': 'Kelayakan_Timeline',     'bobot': 0.25, 'tipe': 'benefit'},
            {'nama': 'Relevansi_Bidang',       'bobot': 0.25, 'tipe': 'benefit'},
            {'nama': 'Dampak_Rencana',         'bobot': 0.20, 'tipe': 'benefit'},
        ]
    },
    'DM3_Wawancara': {
        'label': 'DM 3 — Wawancara',
        'folder': 'DM3_Wawancara',
        'kriteria': [
            {'nama': 'Motivasi_Komitmen',      'bobot': 0.30, 'tipe': 'benefit'},
            {'nama': 'Kemampuan_Komunikasi',   'bobot': 0.25, 'tipe': 'benefit'},
            {'nama': 'Pemahaman_Bidang',       'bobot': 0.25, 'tipe': 'benefit'},
            {'nama': 'Leadership_Potential',   'bobot': 0.20, 'tipe': 'benefit'},
        ]
    }
}


def cek_bahasa(jenis, skor):
    if jenis not in BATAS_BAHASA:
        return False, f'Jenis tes tidak dikenal: {jenis}'
    minimal = BATAS_BAHASA[jenis]
    lolos   = float(skor) >= minimal
    return lolos, (f'{jenis} {skor} >= {minimal} OK' if lolos
                   else f'{jenis} {skor} < {minimal} (min {minimal})')


def verifikasi_administrasi(kandidat):
    flags = []

    ada_rek = pd.notna(kandidat.get('file_rekomendasi')) and bool(kandidat.get('file_rekomendasi'))
    if not ada_rek:
        flags.append('Surat rekomendasi tidak ada')
    elif not bool(kandidat.get('rekomendasi_valid', False)):
        flags.append('Format rekomendasi tidak valid — verifikasi manual')

    usia          = int(kandidat.get('usia', 99))
    sedang_kuliah = bool(kandidat.get('sedang_kuliah', False))
    batas_usia    = BATAS_USIA_KULIAH if sedang_kuliah else BATAS_USIA_UMUM
    if usia > batas_usia:
        flags.append(f'Usia {usia} tahun > batas {batas_usia} tahun')

    ada_loa = pd.notna(kandidat.get('file_loa_surat_aktif')) and bool(kandidat.get('file_loa_surat_aktif'))
    if not ada_loa:
        flags.append('Surat LoA/Surat Aktif tidak ada')
    elif not bool(kandidat.get('loa_valid', False)):
        flags.append('LoA/Surat Aktif tidak valid — verifikasi manual')

    ipk = float(kandidat.get('ipk', 0))
    if ipk < BATAS_IPK:
        flags.append(f'IPK {ipk} < minimal {BATAS_IPK}')

    ukbi = int(kandidat.get('skor_ukbi', 0))
    if ukbi < BATAS_UKBI:
        flags.append(f'UKBI {ukbi} < minimal Unggul ({BATAS_UKBI})')

    jenis_tes = str(kandidat.get('jenis_tes_bahasa', ''))
    skor_tes  = float(kandidat.get('skor_tes_bahasa', 0))
    bahasa_ok, bahasa_pesan = cek_bahasa(jenis_tes, skor_tes)
    if not bahasa_ok:
        flags.append(f'Bahasa asing: {bahasa_pesan}')

    ada_rs = pd.notna(kandidat.get('file_rencana_studi')) and bool(kandidat.get('file_rencana_studi'))
    if not ada_rs:
        flags.append('File rencana studi tidak ada')
    elif not bool(kandidat.get('rencana_studi_valid', False)):
        flags.append('Format rencana studi tidak valid — verifikasi manual')

    ada_esai = pd.notna(kandidat.get('file_esai')) and bool(kandidat.get('file_esai'))
    if not ada_esai:
        flags.append('File esai tidak ada')
    elif not bool(kandidat.get('esai_valid', False)):
        flags.append('Format esai tidak valid — verifikasi manual')

    return {
        'id':   kandidat['id'],
        'nama': kandidat['nama'],
        'flags': flags,
        'lolos_administrasi': len(flags) == 0,
    }


def topsis(matriks, kriteria_list):
    X    = matriks.values.astype(float)
    n, m = X.shape
    norm = np.sqrt((X**2).sum(axis=0))
    norm[norm == 0] = 1e-10
    R    = X / norm
    bobot = np.array([k['bobot'] for k in kriteria_list])
    V     = R * bobot
    A_plus  = np.array([V[:,j].max() if kriteria_list[j]['tipe']=='benefit'
                        else V[:,j].min() for j in range(m)])
    A_minus = np.array([V[:,j].min() if kriteria_list[j]['tipe']=='benefit'
                        else V[:,j].max() for j in range(m)])
    D_plus  = np.sqrt(((V - A_plus) **2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus)**2).sum(axis=1))
    denom   = D_plus + D_minus
    denom[denom == 0] = 1e-10
    return pd.Series(D_minus / denom, index=matriks.index)


def borda_count(ranking_dict, kandidat_ids):
    n      = len(kandidat_ids)
    scores = pd.Series(0.0, index=kandidat_ids)
    for ranking in ranking_dict.values():
        for kid in kandidat_ids:
            scores[kid] += (n - ranking[kid])
    return scores


def load_all():
    df_pendaftar  = pd.read_csv(f'{BASE_DIR}/data_pendaftar.csv')
    pendaftar_raw = df_pendaftar.to_dict('records')

    hasil_admin = [verifikasi_administrasi(p) for p in pendaftar_raw]
    lolos_admin = [p for p, r in zip(pendaftar_raw, hasil_admin)
                   if r['lolos_administrasi']]

    ids_lolos = [p['id']   for p in lolos_admin]
    nama_map  = {p['id']: p['nama'] for p in pendaftar_raw}

    matriks_dm = {}
    for dm_key, dm_val in KRITERIA.items():
        dm_dir  = f'{NILAI_DIR}/{dm_val["folder"]}'
        df_rata = pd.DataFrame(index=ids_lolos)
        for k in dm_val['kriteria']:
            df_a = pd.read_csv(f'{dm_dir}/{k["nama"]}.csv', index_col='id')
            df_a = df_a.loc[df_a.index.isin(ids_lolos)]
            df_rata[k['nama']] = df_a.mean(axis=1)
        matriks_dm[dm_key] = df_rata

    skor_topsis    = {}
    ranking_topsis = {}
    for dm_key, dm_val in KRITERIA.items():
        s = topsis(matriks_dm[dm_key], dm_val['kriteria'])
        skor_topsis[dm_key]    = s
        ranking_topsis[dm_key] = s.rank(ascending=False, method='min').astype(int)

    borda_scores  = borda_count(ranking_topsis, ids_lolos)
    ranking_final = borda_scores.rank(ascending=False, method='min').astype(int)

    df_final = pd.DataFrame({
        'id':   ids_lolos,
        'nama': [nama_map[i] for i in ids_lolos],
    })
    for dm_key, dm_val in KRITERIA.items():
        short = dm_val['label'].split('—')[1].strip()
        df_final[f'rank_{dm_key}']  = [int(ranking_topsis[dm_key][k]) for k in ids_lolos]
        df_final[f'skor_{dm_key}']  = [round(float(skor_topsis[dm_key][k]), 4) for k in ids_lolos]
    df_final['poin_borda']    = borda_scores.values.astype(int)
    df_final['ranking_final'] = ranking_final.values
    df_final = df_final.sort_values('ranking_final').reset_index(drop=True)

    return {
        'pendaftar_raw':  pendaftar_raw,
        'hasil_admin':    hasil_admin,
        'lolos_admin':    lolos_admin,
        'ids_lolos':      ids_lolos,
        'nama_map':       nama_map,
        'matriks_dm':     matriks_dm,
        'skor_topsis':    skor_topsis,
        'ranking_topsis': ranking_topsis,
        'borda_scores':   borda_scores,
        'df_final':       df_final,
    }