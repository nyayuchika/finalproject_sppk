# app.py
# Jalankan: streamlit run app.py

import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import streamlit as st

# ================================================================
# KONFIGURASI HALAMAN
# ================================================================
st.set_page_config(
    page_title='SPK Beasiswa Unggulan',
    page_icon='🎓',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: white; border-radius: 10px; padding: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
    .badge-lolos  { background:#d4edda; color:#155724; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; }
    .badge-tidak  { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; }
    .badge-manual { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; }
    div[data-testid="stSidebar"] { background: #1a3c6e; }
    div[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# KONSTANTA
# ================================================================
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

# ================================================================
# FUNGSI INTI
# ================================================================
def cek_bahasa(jenis, skor):
    if jenis not in BATAS_BAHASA:
        return False, f'Jenis tes tidak dikenal: {jenis}'
    minimal = BATAS_BAHASA[jenis]
    lolos = float(skor) >= minimal
    return lolos, (f'{jenis} {skor} ≥ {minimal} ✓' if lolos
                   else f'{jenis} {skor} < {minimal} (min {minimal})')

def verifikasi_administrasi(kandidat):
    flags = []

    ada_rek = pd.notna(kandidat.get('file_rekomendasi')) and bool(kandidat.get('file_rekomendasi'))
    if not ada_rek:
        flags.append('Surat rekomendasi tidak ada')
    elif not bool(kandidat.get('rekomendasi_valid', False)):
        flags.append('Format rekomendasi tidak valid — verifikasi manual')

    usia = int(kandidat.get('usia', 99))
    sedang_kuliah = bool(kandidat.get('sedang_kuliah', False))
    batas_usia = BATAS_USIA_KULIAH if sedang_kuliah else BATAS_USIA_UMUM
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
    X = matriks.values.astype(float)
    n, m = X.shape
    norm = np.sqrt((X ** 2).sum(axis=0))
    norm[norm == 0] = 1e-10
    R = X / norm
    bobot = np.array([k['bobot'] for k in kriteria_list])
    V = R * bobot
    A_plus  = np.array([V[:, j].max() if kriteria_list[j]['tipe'] == 'benefit'
                        else V[:, j].min() for j in range(m)])
    A_minus = np.array([V[:, j].min() if kriteria_list[j]['tipe'] == 'benefit'
                        else V[:, j].max() for j in range(m)])
    D_plus  = np.sqrt(((V - A_plus)  ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    denom   = D_plus + D_minus
    denom[denom == 0] = 1e-10
    Ci = D_minus / denom
    return pd.Series(Ci, index=matriks.index, name='Skor_TOPSIS')

def borda_count(ranking_dict, kandidat_ids):
    n = len(kandidat_ids)
    scores = pd.Series(0.0, index=kandidat_ids)
    for ranking in ranking_dict.values():
        for kid in kandidat_ids:
            scores[kid] += (n - ranking[kid])
    return scores

# ================================================================
# LOAD & PROSES DATA (di-cache agar tidak reload tiap interaksi)
# ================================================================
@st.cache_data
def load_and_process():
    df_pendaftar  = pd.read_csv(f'{BASE_DIR}/data_pendaftar.csv')
    pendaftar_raw = df_pendaftar.to_dict('records')

    # Tahap 1 — Administrasi
    hasil_admin = [verifikasi_administrasi(p) for p in pendaftar_raw]
    lolos_admin = [p for p, r in zip(pendaftar_raw, hasil_admin) if r['lolos_administrasi']]

    ids_lolos = [p['id']   for p in lolos_admin]
    nama_map  = {p['id']: p['nama'] for p in pendaftar_raw}

    # Tahap 2 — Baca matriks penilaian
    matriks_dm = {}
    for dm_key, dm_val in KRITERIA.items():
        dm_dir   = f'{NILAI_DIR}/{dm_val["folder"]}'
        df_rata  = pd.DataFrame(index=ids_lolos)
        for k in dm_val['kriteria']:
            df_asesor = pd.read_csv(f'{dm_dir}/{k["nama"]}.csv', index_col='id')
            df_asesor = df_asesor.loc[df_asesor.index.isin(ids_lolos)]
            df_rata[k['nama']] = df_asesor.mean(axis=1)
        matriks_dm[dm_key] = df_rata

    # TOPSIS
    skor_topsis    = {}
    ranking_topsis = {}
    for dm_key, dm_val in KRITERIA.items():
        skor = topsis(matriks_dm[dm_key], dm_val['kriteria'])
        skor_topsis[dm_key]    = skor
        ranking_topsis[dm_key] = skor.rank(ascending=False, method='min').astype(int)

    # BORDA
    borda_scores  = borda_count(ranking_topsis, ids_lolos)
    ranking_final = borda_scores.rank(ascending=False, method='min').astype(int)

    df_final = pd.DataFrame({'ID': ids_lolos,
                              'Nama': [nama_map[i] for i in ids_lolos]})
    for dm_key, dm_val in KRITERIA.items():
        label = 'Rank ' + dm_val['label'].split('—')[1].strip()
        df_final[label] = [ranking_topsis[dm_key][kid] for kid in ids_lolos]
        df_final['Skor ' + dm_val['label'].split('—')[1].strip()] = \
            [round(skor_topsis[dm_key][kid], 4) for kid in ids_lolos]

    df_final['Total Poin Borda'] = borda_scores.values.astype(int)
    df_final['Ranking Final']    = ranking_final.values
    df_final = df_final.sort_values('Ranking Final').reset_index(drop=True)
    df_final.index += 1

    return (pendaftar_raw, hasil_admin, lolos_admin,
            matriks_dm, skor_topsis, ranking_topsis,
            borda_scores, df_final, nama_map)

# ================================================================
# SIDEBAR NAVIGASI
# ================================================================
st.sidebar.markdown('## 🎓 SPK Beasiswa Unggulan')
st.sidebar.markdown('---')
menu = st.sidebar.radio('Navigasi', [
    '📊 Dashboard',
    '📋 Verifikasi Administrasi',
    '🏆 Ranking Substansi',
    '👤 Profil Kandidat',
    '📥 Export Laporan',
])
st.sidebar.markdown('---')
st.sidebar.markdown('**Metode:** TOPSIS + BORDA')
st.sidebar.markdown('**Data:** 100 Pendaftar')

# Cek apakah data tersedia
if not os.path.exists(f'{BASE_DIR}/data_pendaftar.csv'):
    st.error('❌ Data belum tersedia. Jalankan dulu: `python generate_data.py`')
    st.stop()

# Load data
(pendaftar_raw, hasil_admin, lolos_admin,
 matriks_dm, skor_topsis, ranking_topsis,
 borda_scores, df_final, nama_map) = load_and_process()

n_total  = len(pendaftar_raw)
n_lolos  = len(lolos_admin)
n_tidak  = n_total - n_lolos


# ================================================================
# HALAMAN 1 — DASHBOARD
# ================================================================
if menu == '📊 Dashboard':
    st.title('📊 Dashboard SPK Beasiswa Unggulan')
    st.markdown('Sistem Pendukung Keputusan seleksi penerima Beasiswa Unggulan.')

    # Metrik utama
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Total Pendaftar',       n_total)
    c2.metric('Lolos Administrasi',    n_lolos,  delta=f'{n_lolos/n_total*100:.0f}%')
    c3.metric('Tidak Lolos Admin',     n_tidak,  delta=f'-{n_tidak}', delta_color='inverse')
    c4.metric('Kandidat Substansi',    n_lolos)

    st.markdown('---')
    col1, col2 = st.columns(2)

    # Pie chart administrasi
    with col1:
        st.subheader('Distribusi Hasil Administrasi')
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie([n_lolos, n_tidak],
               labels=[f'Lolos ({n_lolos})', f'Tidak Lolos ({n_tidak})'],
               colors=['#2ecc71', '#e74c3c'],
               autopct='%1.1f%%', startangle=90,
               textprops={'fontsize': 11})
        ax.set_title('Tahap Administrasi', fontweight='bold')
        st.pyplot(fig)
        plt.close()

    # Bar chart jenis masalah
    with col2:
        st.subheader('Jenis Masalah Administrasi')
        kat_flags = {
            'Rekomendasi': 0, 'Usia': 0, 'LoA/Aktif': 0,
            'IPK': 0, 'UKBI': 0, 'Bahasa Asing': 0,
            'Rencana Studi': 0, 'Esai': 0
        }
        mapping = {
            'rekomendasi': 'Rekomendasi', 'usia': 'Usia', 'loa': 'LoA/Aktif',
            'ipk': 'IPK', 'ukbi': 'UKBI', 'bahasa': 'Bahasa Asing',
            'rencana studi': 'Rencana Studi', 'esai': 'Esai'
        }
        for r in hasil_admin:
            for f in r['flags']:
                for kw, kat in mapping.items():
                    if kw in f.lower():
                        kat_flags[kat] += 1
                        break
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        cats = list(kat_flags.keys())
        vals = list(kat_flags.values())
        colors_b = ['#e74c3c' if v > 0 else '#bdc3c7' for v in vals]
        bars = ax2.barh(cats, vals, color=colors_b)
        ax2.set_xlabel('Jumlah Pendaftar')
        ax2.set_title('Jenis Pelanggaran Administrasi', fontweight='bold')
        ax2.set_xlim(0, max(vals) + 3)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax2.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
                         str(val), va='center', fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    st.markdown('---')
    st.subheader('Distribusi Skor TOPSIS per DM')
    fig3, axes3 = plt.subplots(1, 3, figsize=(15, 4))
    for idx, (dm_key, dm_val) in enumerate(KRITERIA.items()):
        skor = skor_topsis[dm_key]
        axes3[idx].hist(skor.values, bins=15, color='#3498db', edgecolor='white', alpha=0.85)
        axes3[idx].set_title(dm_val['label'], fontweight='bold')
        axes3[idx].set_xlabel('Skor TOPSIS')
        axes3[idx].set_ylabel('Frekuensi')
        axes3[idx].axvline(skor.mean(), color='red', linestyle='--',
                           label=f'Rata-rata: {skor.mean():.3f}')
        axes3[idx].legend(fontsize=9)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

    st.markdown('---')
    st.subheader('Top 10 Kandidat Terbaik (Ranking Final Borda)')
    top10 = df_final.head(10)[['ID', 'Nama', 'Total Poin Borda', 'Ranking Final']]
    st.dataframe(top10, use_container_width=True)


# ================================================================
# HALAMAN 2 — VERIFIKASI ADMINISTRASI
# ================================================================
elif menu == '📋 Verifikasi Administrasi':
    st.title('📋 Verifikasi Administrasi')

    tab1, tab2 = st.tabs(['📄 Semua Pendaftar', '🔴 Perlu Verifikasi Manual'])

    df_admin = pd.DataFrame([{
        'ID':     r['id'],
        'Nama':   r['nama'],
        'Status': 'LOLOS' if r['lolos_administrasi'] else 'TIDAK LOLOS',
        'Jumlah Masalah': len(r['flags']),
        'Detail Masalah': ' | '.join(r['flags']) if r['flags'] else '-'
    } for r in hasil_admin])

    with tab1:
        st.markdown(f'**Total: {n_total} pendaftar** | '
                    f'✅ Lolos: {n_lolos} | ❌ Tidak Lolos: {n_tidak}')

        # Filter
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            filter_status = st.selectbox('Filter Status',
                                         ['Semua', 'LOLOS', 'TIDAK LOLOS'])
        with col_f2:
            search = st.text_input('🔍 Cari nama / ID')

        df_show = df_admin.copy()
        if filter_status != 'Semua':
            df_show = df_show[df_show['Status'] == filter_status]
        if search:
            mask = (df_show['Nama'].str.contains(search, case=False) |
                    df_show['ID'].str.contains(search, case=False))
            df_show = df_show[mask]

        def warnai_status(val):
            if val == 'LOLOS':
                return 'background-color: #d4edda; color: #155724; font-weight: bold'
            return 'background-color: #f8d7da; color: #721c24; font-weight: bold'

        st.dataframe(
            df_show.style.applymap(warnai_status, subset=['Status']),
            use_container_width=True, height=500
        )

    with tab2:
        st.markdown('Kandidat berikut memiliki flag merah dan memerlukan pengecekan manual oleh petugas.')
        perlu_manual = [r for r in hasil_admin if not r['lolos_administrasi']]

        for r in perlu_manual:
            with st.expander(f"🔴 {r['id']} — {r['nama']} ({len(r['flags'])} masalah)"):
                for f in r['flags']:
                    st.error(f'❌ {f}')


# ================================================================
# HALAMAN 3 — RANKING SUBSTANSI
# ================================================================
elif menu == '🏆 Ranking Substansi':
    st.title('🏆 Ranking Substansi')

    tab1, tab2, tab3 = st.tabs(['🥇 Ranking Final (BORDA)', '📐 Skor TOPSIS per DM', '📊 Visualisasi'])

    with tab1:
        st.markdown(f'**{n_lolos} kandidat** lolos administrasi dan masuk tahap substansi.')

        kuota = st.slider('Kuota Beasiswa', min_value=1, max_value=min(30, n_lolos),
                          value=10, step=1)

        df_show = df_final.copy()
        df_show.insert(0, 'Keterangan',
                       df_show['Ranking Final'].apply(
                           lambda r: '🏆 Penerima' if r <= kuota
                           else ('📋 Cadangan' if r <= kuota + 5 else '—')
                       ))

        def warnai_ranking(val):
            if val == '🏆 Penerima':  return 'background-color:#d4edda;color:#155724;font-weight:bold'
            if val == '📋 Cadangan':  return 'background-color:#fff3cd;color:#856404;font-weight:bold'
            return ''

        st.dataframe(
            df_show.style.applymap(warnai_ranking, subset=['Keterangan']),
            use_container_width=True, height=550
        )

    with tab2:
        st.markdown('Skor TOPSIS masing-masing DM sebelum diagregasi dengan metode Borda.')
        dm_pilih = st.selectbox('Pilih DM', list(KRITERIA.keys()),
                                format_func=lambda k: KRITERIA[k]['label'])

        skor  = skor_topsis[dm_pilih]
        rank  = ranking_topsis[dm_pilih]
        df_tp = pd.DataFrame({
            'ID':          skor.index,
            'Nama':        [nama_map[i] for i in skor.index],
            'Skor TOPSIS': skor.round(4).values,
            'Ranking':     rank.values
        }).sort_values('Ranking').reset_index(drop=True)
        df_tp.index += 1

        st.dataframe(df_tp, use_container_width=True, height=500)

    with tab3:
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            st.subheader('Top 15 — Skor TOPSIS')
            dm_vis = st.selectbox('DM', list(KRITERIA.keys()),
                                  format_func=lambda k: KRITERIA[k]['label'],
                                  key='vis_dm')
            skor_v = skor_topsis[dm_vis]
            top15  = skor_v.sort_values(ascending=False).head(15)
            fig_v, ax_v = plt.subplots(figsize=(6, 5))
            import seaborn as sns
            palette = sns.color_palette('Blues_d', 15)
            t_nama = [nama_map[i][:16] for i in top15.index]
            ax_v.barh(t_nama[::-1], top15.values[::-1], color=palette)
            ax_v.set_xlabel('Skor TOPSIS')
            ax_v.set_title(KRITERIA[dm_vis]['label'], fontweight='bold')
            ax_v.set_xlim(0, 1.05)
            plt.tight_layout()
            st.pyplot(fig_v)
            plt.close()

        with col_v2:
            st.subheader('Top 20 — Poin Borda Final')
            kuota_v = st.slider('Tandai kuota', 1, 30, 10, key='vis_kuota')
            top20_ids  = borda_scores.sort_values(ascending=False).head(20).index
            top20_nama = [nama_map[i][:16] for i in top20_ids]
            top20_vals = borda_scores[top20_ids].values
            colors_b   = ['#f1c40f' if i < kuota_v else
                          ('#bdc3c7' if i < kuota_v + 5 else '#5dade2')
                          for i in range(len(top20_ids))]
            fig_b, ax_b = plt.subplots(figsize=(6, 5))
            ax_b.barh(top20_nama[::-1], top20_vals[::-1], color=colors_b[::-1])
            ax_b.set_xlabel('Total Poin Borda')
            ax_b.set_title('Ranking Final BORDA', fontweight='bold')
            for i, (nm, vl) in enumerate(zip(top20_nama[::-1], top20_vals[::-1])):
                ax_b.text(vl + 0.1, i, str(int(vl)), va='center', fontsize=9)
            plt.tight_layout()
            st.pyplot(fig_b)
            plt.close()


# ================================================================
# HALAMAN 4 — PROFIL KANDIDAT
# ================================================================
elif menu == '👤 Profil Kandidat':
    st.title('👤 Profil Detail Kandidat')

    opsi_kandidat = {f"{kid} — {nama_map[kid]}": kid for kid in
                     [p['id'] for p in lolos_admin]}
    pilihan = st.selectbox('Pilih Kandidat', list(opsi_kandidat.keys()))
    kid_id  = opsi_kandidat[pilihan]

    # Data dasar
    data_p = next(p for p in pendaftar_raw if p['id'] == kid_id)
    rank_f = int(df_final[df_final['ID'] == kid_id]['Ranking Final'].values[0])
    poin_b = int(borda_scores[kid_id])

    st.markdown('---')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Ranking Final', f'#{rank_f}')
    c2.metric('Total Poin Borda', poin_b)
    c3.metric('IPK', data_p['ipk'])
    c4.metric('UKBI', data_p['skor_ukbi'])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader('📄 Data Administrasi')
        res_admin = next(r for r in hasil_admin if r['id'] == kid_id)
        status_adm = '✅ LOLOS' if res_admin['lolos_administrasi'] else '❌ TIDAK LOLOS'
        st.markdown(f'**Status Administrasi:** {status_adm}')

        tabel_adm = {
            'Kriteria': ['Usia', 'IPK', 'UKBI',
                         f'Bahasa ({data_p["jenis_tes_bahasa"]})',
                         'Rekomendasi', 'LoA/Surat Aktif',
                         'Rencana Studi', 'Esai'],
            'Nilai': [
                data_p['usia'],
                data_p['ipk'],
                data_p['skor_ukbi'],
                data_p['skor_tes_bahasa'],
                '✅ Ada' if pd.notna(data_p.get('file_rekomendasi')) and data_p.get('file_rekomendasi') else '❌ Tidak Ada',
                '✅ Ada' if pd.notna(data_p.get('file_loa_surat_aktif')) and data_p.get('file_loa_surat_aktif') else '❌ Tidak Ada',
                '✅ Ada' if pd.notna(data_p.get('file_rencana_studi')) and data_p.get('file_rencana_studi') else '❌ Tidak Ada',
                '✅ Ada' if pd.notna(data_p.get('file_esai')) and data_p.get('file_esai') else '❌ Tidak Ada',
            ],
            'Status': [
                '✅' if data_p['usia'] <= (BATAS_USIA_KULIAH if data_p['sedang_kuliah'] else BATAS_USIA_UMUM) else '❌',
                '✅' if data_p['ipk'] >= BATAS_IPK else '❌',
                '✅' if data_p['skor_ukbi'] >= BATAS_UKBI else '❌',
                '✅' if cek_bahasa(data_p['jenis_tes_bahasa'], data_p['skor_tes_bahasa'])[0] else '❌',
                '✅' if data_p.get('rekomendasi_valid') else '❌',
                '✅' if data_p.get('loa_valid') else '❌',
                '✅' if data_p.get('rencana_studi_valid') else '❌',
                '✅' if data_p.get('esai_valid') else '❌',
            ]
        }
        st.dataframe(pd.DataFrame(tabel_adm), use_container_width=True, hide_index=True)

        st.subheader('📐 Skor TOPSIS per DM')
        for dm_key, dm_val in KRITERIA.items():
            skor_k = round(skor_topsis[dm_key][kid_id], 4)
            rank_k = int(ranking_topsis[dm_key][kid_id])
            st.markdown(f'**{dm_val["label"]}:** Skor `{skor_k}` — Ranking `#{rank_k}`')

    with col2:
        st.subheader('🕸️ Radar Chart Substansi')
        subkrit, nilai = [], []
        for dm_key, dm_val in KRITERIA.items():
            for k in dm_val['kriteria']:
                subkrit.append(k['nama'].replace('_', ' ')[:14])
                nilai.append(matriks_dm[dm_key].loc[kid_id, k['nama']])

        N = len(subkrit)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles    += angles[:1]
        nilai_plot = nilai + nilai[:1]

        fig_r, ax_r = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))
        ax_r.fill(angles, nilai_plot, alpha=0.25, color='#2980b9')
        ax_r.plot(angles, nilai_plot, color='#2980b9', linewidth=2, marker='o', markersize=4)
        ax_r.set_xticks(angles[:-1])
        ax_r.set_xticklabels(subkrit, size=8)
        ax_r.set_ylim(0, 10)
        ax_r.set_title(f'{kid_id} — {nama_map[kid_id]}', pad=20, fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig_r)
        plt.close()


# ================================================================
# HALAMAN 5 — EXPORT LAPORAN
# ================================================================
elif menu == '📥 Export Laporan':
    st.title('📥 Export Laporan')

    kuota_exp = st.slider('Kuota Beasiswa untuk laporan', 1, min(30, n_lolos), 10)

    tab1, tab2, tab3 = st.tabs([
        '📋 Laporan Administrasi',
        '🏆 Laporan Substansi',
        '📊 Laporan Lengkap'
    ])

    with tab1:
        df_adm_exp = pd.DataFrame([{
            'ID':     r['id'],
            'Nama':   r['nama'],
            'Status': 'LOLOS' if r['lolos_administrasi'] else 'TIDAK LOLOS',
            'Masalah': ' | '.join(r['flags']) if r['flags'] else '-'
        } for r in hasil_admin])

        st.dataframe(df_adm_exp, use_container_width=True)

        csv1 = df_adm_exp.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='⬇️ Download CSV Administrasi',
            data=csv1,
            file_name='laporan_administrasi.csv',
            mime='text/csv'
        )

    with tab2:
        df_sub_exp = df_final.copy()
        df_sub_exp.insert(0, 'Keterangan',
                          df_sub_exp['Ranking Final'].apply(
                              lambda r: 'Penerima' if r <= kuota_exp
                              else ('Cadangan' if r <= kuota_exp + 5 else '-')
                          ))

        st.dataframe(df_sub_exp, use_container_width=True)

        csv2 = df_sub_exp.to_csv(index=True).encode('utf-8')
        st.download_button(
            label='⬇️ Download CSV Substansi',
            data=csv2,
            file_name='laporan_substansi_final.csv',
            mime='text/csv'
        )

    with tab3:
        df_topsis_all = pd.DataFrame({
            dm_val['label']: skor_topsis[dm_key].round(4)
            for dm_key, dm_val in KRITERIA.items()
        })
        df_topsis_all.insert(0, 'Nama', [nama_map[i] for i in df_topsis_all.index])
        df_topsis_all.insert(0, 'ID',   df_topsis_all.index)

        df_merged = df_topsis_all.merge(
            df_final[['ID','Ranking Final','Total Poin Borda']],
            on='ID', how='left'
        ).sort_values('Ranking Final')

        st.dataframe(df_merged, use_container_width=True)

        csv3 = df_merged.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='⬇️ Download CSV Lengkap (TOPSIS + BORDA)',
            data=csv3,
            file_name='laporan_lengkap_spk.csv',
            mime='text/csv'
        )

    st.markdown('---')
    st.info('💡 Untuk export ke Excel, buka CSV di Excel atau tambahkan `df.to_excel()` di kode.')