# app.py
# Jalankan: python app.py

from flask import Flask, render_template, request, jsonify, Response
import pandas as pd
import numpy as np
import json
import io
import os
from spk_engine import load_all, KRITERIA, BATAS_BAHASA, BATAS_IPK, BATAS_UKBI, cek_bahasa

app = Flask(__name__)

# Load sekali saat server start
DATA = load_all()


def get_flag_counts():
    mapping = {
        'rekomendasi': 'Rekomendasi', 'usia': 'Usia', 'loa': 'LoA/Aktif',
        'ipk': 'IPK', 'ukbi': 'UKBI', 'bahasa': 'Bahasa Asing',
        'rencana studi': 'Rencana Studi', 'esai': 'Esai'
    }
    counts = {v: 0 for v in mapping.values()}
    for r in DATA['hasil_admin']:
        for f in r['flags']:
            for kw, kat in mapping.items():
                if kw in f.lower():
                    counts[kat] += 1
                    break
    return counts


# ================================================================
# DASHBOARD
# ================================================================
@app.route('/')
def dashboard():
    n_total = len(DATA['pendaftar_raw'])
    n_lolos = len(DATA['lolos_admin'])
    n_tidak = n_total - n_lolos

    flag_counts = get_flag_counts()

    # Data untuk chart pie administrasi
    pie_data = {
        'labels': ['Lolos', 'Tidak Lolos'],
        'values': [n_lolos, n_tidak],
        'colors': ['#2ecc71', '#e74c3c']
    }

    # Data untuk chart bar masalah
    bar_data = {
        'labels': list(flag_counts.keys()),
        'values': list(flag_counts.values()),
    }

    # Data untuk histogram distribusi skor TOPSIS
    hist_data = {}
    for dm_key, dm_val in KRITERIA.items():
        skor = DATA['skor_topsis'][dm_key]
        hist_data[dm_val['label']] = {
            'values': [round(float(v), 4) for v in skor.values],
            'mean':   round(float(skor.mean()), 4),
        }

    # Top 10
    top10 = DATA['df_final'].head(10)[['id','nama','poin_borda','ranking_final']].to_dict('records')

    return render_template('dashboard.html',
        n_total=n_total, n_lolos=n_lolos, n_tidak=n_tidak,
        pie_data=json.dumps(pie_data),
        bar_data=json.dumps(bar_data),
        hist_data=json.dumps(hist_data),
        top10=top10,
    )


# ================================================================
# ADMINISTRASI
# ================================================================
@app.route('/administrasi')
def administrasi():
    status_filter = request.args.get('status', 'semua')
    search        = request.args.get('search', '').lower()

    rows = []
    for r in DATA['hasil_admin']:
        if status_filter == 'lolos'  and not r['lolos_administrasi']: continue
        if status_filter == 'tidak'  and r['lolos_administrasi']:     continue
        if search and search not in r['nama'].lower() and search not in r['id'].lower(): continue
        rows.append(r)

    return render_template('administrasi.html',
        rows=rows,
        status_filter=status_filter,
        search=search,
        n_total=len(DATA['pendaftar_raw']),
        n_lolos=len(DATA['lolos_admin']),
        n_tidak=len(DATA['pendaftar_raw']) - len(DATA['lolos_admin']),
    )


# ================================================================
# SUBSTANSI
# ================================================================
@app.route('/substansi')
def substansi():
    kuota  = int(request.args.get('kuota', 10))
    dm_sel = request.args.get('dm', 'DM1_Esai')

    df = DATA['df_final'].copy()
    df['keterangan'] = df['ranking_final'].apply(
        lambda r: 'Penerima' if r <= kuota
        else ('Cadangan' if r <= kuota+5 else '-')
    )
    rows_final = df.to_dict('records')

    # Tabel TOPSIS DM terpilih
    skor  = DATA['skor_topsis'][dm_sel]
    rank  = DATA['ranking_topsis'][dm_sel]
    topsis_rows = sorted([{
        'id':     kid,
        'nama':   DATA['nama_map'][kid],
        'skor':   round(float(skor[kid]), 4),
        'ranking': int(rank[kid])
    } for kid in DATA['ids_lolos']], key=lambda x: x['ranking'])

    # Data chart Borda top 20
    top20_ids  = DATA['borda_scores'].sort_values(ascending=False).head(20).index.tolist()
    borda_chart = {
        'labels': [DATA['nama_map'][i] for i in top20_ids],
        'values': [int(DATA['borda_scores'][i]) for i in top20_ids],
        'colors': ['#f1c40f' if DATA['ranking_topsis']['DM1_Esai'][i] <= kuota
                   else '#5dade2' for i in top20_ids],
    }

    # Data chart TOPSIS top 15
    top15_ids = skor.sort_values(ascending=False).head(15).index.tolist()
    topsis_chart = {
        'labels': [DATA['nama_map'][i] for i in top15_ids],
        'values': [round(float(skor[i]), 4) for i in top15_ids],
    }

    return render_template('substansi.html',
        rows_final=rows_final,
        topsis_rows=topsis_rows,
        dm_sel=dm_sel,
        kuota=kuota,
        kriteria_list=KRITERIA,
        borda_chart=json.dumps(borda_chart),
        topsis_chart=json.dumps(topsis_chart),
        n_lolos=len(DATA['lolos_admin']),
    )


# ================================================================
# PROFIL KANDIDAT
# ================================================================
@app.route('/profil')
def profil():
    kid_id = request.args.get('id', DATA['ids_lolos'][0])

    data_p  = next(p for p in DATA['pendaftar_raw'] if p['id'] == kid_id)
    res_adm = next(r for r in DATA['hasil_admin']   if r['id'] == kid_id)
    row_f   = DATA['df_final'][DATA['df_final']['id'] == kid_id].iloc[0]

    # Radar chart data
    subkrit, nilai = [], []
    for dm_key, dm_val in KRITERIA.items():
        for k in dm_val['kriteria']:
            subkrit.append(k['nama'].replace('_',' '))
            nilai.append(round(float(DATA['matriks_dm'][dm_key].loc[kid_id, k['nama']]), 2))

    radar_data = json.dumps({'labels': subkrit, 'values': nilai})

    # Tabel TOPSIS per DM
    dm_scores = []
    for dm_key, dm_val in KRITERIA.items():
        dm_scores.append({
            'label':   dm_val['label'],
            'skor':    round(float(DATA['skor_topsis'][dm_key][kid_id]), 4),
            'ranking': int(DATA['ranking_topsis'][dm_key][kid_id]),
        })

    # Tabel administrasi
    batas_usia = 33 if data_p['sedang_kuliah'] else 32
    adm_checks = [
        {'kriteria': 'Usia',
         'nilai': str(data_p['usia']) + ' tahun',
         'batas': f'<= {batas_usia} tahun',
         'ok': int(data_p['usia']) <= batas_usia},
        {'kriteria': 'IPK',
         'nilai': str(data_p['ipk']),
         'batas': f'>= {BATAS_IPK}',
         'ok': float(data_p['ipk']) >= BATAS_IPK},
        {'kriteria': 'UKBI',
         'nilai': str(data_p['skor_ukbi']),
         'batas': f'>= {BATAS_UKBI} (Unggul)',
         'ok': int(data_p['skor_ukbi']) >= BATAS_UKBI},
        {'kriteria': f'Bahasa ({data_p["jenis_tes_bahasa"]})',
         'nilai': str(data_p['skor_tes_bahasa']),
         'batas': f'>= {BATAS_BAHASA.get(data_p["jenis_tes_bahasa"], "?")}',
         'ok': cek_bahasa(data_p['jenis_tes_bahasa'], data_p['skor_tes_bahasa'])[0]},
        {'kriteria': 'Rekomendasi',
         'nilai': 'Ada' if data_p.get('file_rekomendasi') else 'Tidak Ada',
         'batas': 'Wajib Ada & Valid',
         'ok': bool(data_p.get('rekomendasi_valid'))},
        {'kriteria': 'LoA/Surat Aktif',
         'nilai': 'Ada' if data_p.get('file_loa_surat_aktif') else 'Tidak Ada',
         'batas': 'Wajib Ada & Valid',
         'ok': bool(data_p.get('loa_valid'))},
        {'kriteria': 'Rencana Studi',
         'nilai': 'Ada' if data_p.get('file_rencana_studi') else 'Tidak Ada',
         'batas': 'Wajib Ada & Valid',
         'ok': bool(data_p.get('rencana_studi_valid'))},
        {'kriteria': 'Esai',
         'nilai': 'Ada' if data_p.get('file_esai') else 'Tidak Ada',
         'batas': 'Wajib Ada & Valid',
         'ok': bool(data_p.get('esai_valid'))},
    ]

    return render_template('profil.html',
        kandidat_list=DATA['ids_lolos'],
        nama_map=DATA['nama_map'],
        kid_id=kid_id,
        data_p=data_p,
        res_adm=res_adm,
        row_f=row_f,
        adm_checks=adm_checks,
        dm_scores=dm_scores,
        radar_data=radar_data,
    )


# ================================================================
# EXPORT
# ================================================================
@app.route('/export')
def export():
    kuota = int(request.args.get('kuota', 10))
    return render_template('export.html', kuota=kuota,
                           n_lolos=len(DATA['lolos_admin']))


@app.route('/export/csv/<jenis>')
def export_csv(jenis):
    kuota = int(request.args.get('kuota', 10))

    if jenis == 'administrasi':
        rows = [{'ID': r['id'], 'Nama': r['nama'],
                 'Status': 'LOLOS' if r['lolos_administrasi'] else 'TIDAK LOLOS',
                 'Masalah': ' | '.join(r['flags']) if r['flags'] else '-'}
                for r in DATA['hasil_admin']]
        df  = pd.DataFrame(rows)
        fname = 'laporan_administrasi.csv'

    elif jenis == 'substansi':
        df = DATA['df_final'].copy()
        df.insert(0, 'Keterangan', df['ranking_final'].apply(
            lambda r: 'Penerima' if r <= kuota
            else ('Cadangan' if r <= kuota+5 else '-')
        ))
        df.columns = [c.replace('_', ' ').title() for c in df.columns]
        fname = 'laporan_substansi.csv'

    else:  # lengkap
        df_t = pd.DataFrame({
            dm_val['label']: DATA['skor_topsis'][dm_key].round(4)
            for dm_key, dm_val in KRITERIA.items()
        })
        df_t.insert(0, 'Nama', [DATA['nama_map'][i] for i in df_t.index])
        df_t.insert(0, 'ID',   df_t.index)
        df = df_t.merge(
            DATA['df_final'][['id','poin_borda','ranking_final']],
            left_on='ID', right_on='id', how='left'
        ).sort_values('ranking_final').drop(columns='id')
        fname = 'laporan_lengkap_spk.csv'

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return Response(buf.getvalue(),
                    mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={fname}'})


if __name__ == '__main__':
    if not os.path.exists('data/data_pendaftar.csv'):
        print('❌ Data belum ada. Jalankan dulu: python generate_data.py')
    else:
        app.run(debug=True, port=5000)