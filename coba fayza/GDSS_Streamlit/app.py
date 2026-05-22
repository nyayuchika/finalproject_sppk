import streamlit as st
import pandas as pd
import numpy as np

st.title("DSS-GDSS Beasiswa Unggulan")

st.write("Prototype Sistem Seleksi Beasiswa")

# =========================
# UPLOAD FILE ADMIN
# =========================

admin_file = st.file_uploader(
    "Upload File Administrasi",
    type=['csv']
)

# =========================
# JIKA FILE ADMIN ADA
# =========================

if admin_file is not None:

    # Read CSV admin
    admin = pd.read_csv(admin_file)

    st.subheader("Data Administrasi")

    st.dataframe(admin)

    # =========================
    # BUTTON PROSES ADMIN
    # =========================

if st.button("Tahap 1: Proses Administrasi"):

    # cek apakah file admin sudah diupload
    if admin_file is None:

        st.warning(
            "Data administrasi belum diupload. "
            "Data belum dapat diproses."
        )

    else:

        st.success("Proses Seleksi Dimulai")

        lolos_admin = admin[
            (admin['ipk'] >= 3.00) &
            (admin['ielts'] >= 6.5) &
            (admin['usia'] <= 32) &
            (admin['rekomendasi'] == 1) &
            (admin['loa'] == 1)
        ]

        st.session_state['lolos_admin'] = lolos_admin
# =========================
# TAMPILKAN LOLOS ADMIN
# =========================

if 'lolos_admin' in st.session_state:

    st.subheader("Peserta Lolos Administrasi")

    st.dataframe(
        st.session_state['lolos_admin']
    )

    # =========================
    # UPLOAD FILE SUBSTANSI
    # =========================

    esai_file = st.file_uploader(
        "Upload File Esai",
        type=['csv']
    )

    wawancara_file = st.file_uploader(
        "Upload File Wawancara",
        type=['csv']
    )

    rencana_file = st.file_uploader(
        "Upload File Rencana Studi",
        type=['csv']
    )

    # =========================
    # JIKA SEMUA FILE ADA
    # =========================

    if (
        esai_file is not None and
        wawancara_file is not None and
        rencana_file is not None
    ):

        esai = pd.read_csv(esai_file)
        wawancara = pd.read_csv(wawancara_file)
        rencana = pd.read_csv(rencana_file)

        st.success("Semua file substansi berhasil diupload!")

        st.subheader("Data Esai")
        st.dataframe(esai)

        st.subheader("Data Wawancara")
        st.dataframe(wawancara)

        st.subheader("Data Rencana Studi")
        st.dataframe(rencana)

if st.button("Tahap 2: Proses DSS-GDSS Seleksi Substansi"):
 # cek apakah admin sudah diproses
    if 'lolos_admin' not in st.session_state:

        st.warning(
            "Tahap administrasi belum selesai. "
            "Silakan proses administrasi terlebih dahulu."
        )

    else:

        st.success("Proses Seleksi Dimulai")

        # =========================
        # AHP ESAI
        # =========================

        st.subheader("Bobot AHP Esai")

        pairwise = np.array([
            [1,   1/2, 1/3, 1/4],
            [2,   1,   1/2, 1/3],
            [3,   2,   1,   1/2],
            [4,   3,   2,   1]
        ])

        col_sum = pairwise.sum(axis=0)

        normalized = pairwise / col_sum

        weights = normalized.mean(axis=1)

        kriteria_e = [
            'tema',
            'tujuan',
            'orisinalitas',
            'kontribusi'
        ]

        # Dataframe bobot
        bobot_esai = pd.DataFrame({
            'Subkriteria': kriteria_e,
            'Bobot': weights
        })

        st.dataframe(bobot_esai)
        st.session_state['bobot_esai'] = bobot_esai

        # =========================
        # AHP WAWANCARA
        # =========================

        st.subheader("Bobot AHP Wawancara")

        pairwise_w = np.array([
            [1,   1/2, 1/3, 2],
            [2,   1,   1/2, 3],
            [3,   2,   1,   4],
            [1/2, 1/3, 1/4, 1]
        ])

        col_sum_w = pairwise_w.sum(axis=0)

        normalized_w = pairwise_w / col_sum_w

        weights_w = normalized_w.mean(axis=1)

        kriteria_w = [
            'komunikasi',
            'motivasi',
            'critical_thinking',
            'prestasi'
        ]

        bobot_wawancara = pd.DataFrame({
            'Subkriteria': kriteria_w,
            'Bobot': weights_w
        })

        st.dataframe(bobot_wawancara)
        st.session_state['bobot_wawancara'] = bobot_wawancara

        # =========================
        # AHP RENCANA STUDI
        # =========================

        st.subheader("Bobot AHP Rencana Studi")

        pairwise_r = np.array([
            [1,   1/2, 1/3],
            [2,   1,   1/2],
            [3,   2,   1]
        ])

        col_sum_r = pairwise_r.sum(axis=0)

        normalized_r = pairwise_r / col_sum_r

        weights_r = normalized_r.mean(axis=1)

        kriteria_r = [
            'alasan_prodi',
            'topik_tesis',
            'roadmap_studi'
        ]

        bobot_rencana = pd.DataFrame({
            'Subkriteria': kriteria_r,
            'Bobot': weights_r
        })

        st.dataframe(bobot_rencana)
        st.session_state['bobot_rencana'] = bobot_rencana

        # =========================
        # TOPSIS ESAI
        # =========================

        st.subheader("Ranking TOPSIS Esai")

        X = esai[kriteria_e].values

        # Normalisasi
        norm = X / np.sqrt((X**2).sum(axis=0))

        # Pembobotan
        weighted = norm * weights

        # Solusi ideal
        ideal_pos = weighted.max(axis=0)
        ideal_neg = weighted.min(axis=0)

        # Jarak solusi ideal
        d_pos = np.sqrt(((weighted - ideal_pos)**2).sum(axis=1))
        d_neg = np.sqrt(((weighted - ideal_neg)**2).sum(axis=1))

        # Nilai preferensi
        score = d_neg / (d_pos + d_neg)

        # Simpan score
        esai['score_esai'] = score

        # Ranking
        esai_rank = esai[
            ['id', 'score_esai']
        ].sort_values(
            by='score_esai',
            ascending=False
        )

        # Tampilkan ranking
        st.dataframe(esai_rank)
        st.session_state['esai_rank'] = esai_rank

        # =========================
        # TOPSIS WAWANCARA
        # =========================

        st.subheader("Ranking TOPSIS Wawancara")

        X_w = wawancara[kriteria_w].values

        # Normalisasi
        norm_w = X_w / np.sqrt((X_w**2).sum(axis=0))

        # Pembobotan
        weighted_w = norm_w * weights_w

        # Solusi ideal
        ideal_pos_w = weighted_w.max(axis=0)
        ideal_neg_w = weighted_w.min(axis=0)

        # Jarak solusi ideal
        d_pos_w = np.sqrt(((weighted_w - ideal_pos_w)**2).sum(axis=1))
        d_neg_w = np.sqrt(((weighted_w - ideal_neg_w)**2).sum(axis=1))

        # Nilai preferensi
        score_w = d_neg_w / (d_pos_w + d_neg_w)

        # Simpan score
        wawancara['score_wawancara'] = score_w

        # Ranking
        wawancara_rank = wawancara[
            ['id', 'score_wawancara']
        ].sort_values(
            by='score_wawancara',
            ascending=False
        )

        # Tampilkan ranking
        st.dataframe(wawancara_rank)
        st.session_state['wawancara_rank'] = wawancara_rank

        # =========================
        # TOPSIS RENCANA STUDI
        # =========================

        st.subheader("Ranking TOPSIS Rencana Studi")

        X_r = rencana[kriteria_r].values

        # Normalisasi
        norm_r = X_r / np.sqrt((X_r**2).sum(axis=0))

        # Pembobotan
        weighted_r = norm_r * weights_r

        # Solusi ideal
        ideal_pos_r = weighted_r.max(axis=0)
        ideal_neg_r = weighted_r.min(axis=0)

        # Jarak solusi ideal
        d_pos_r = np.sqrt(((weighted_r - ideal_pos_r)**2).sum(axis=1))
        d_neg_r = np.sqrt(((weighted_r - ideal_neg_r)**2).sum(axis=1))

        # Nilai preferensi
        score_r = d_neg_r / (d_pos_r + d_neg_r)

        # Simpan score
        rencana['score_rencana'] = score_r

        # Ranking
        rencana_rank = rencana[
            ['id', 'score_rencana']
        ].sort_values(
            by='score_rencana',
            ascending=False
        )

        # Tampilkan ranking
        st.dataframe(rencana_rank)
        st.session_state['rencana_rank'] = rencana_rank

        # =========================
        # MEMBUAT RANKING OTOMATIS
        # =========================

        st.subheader("Ranking Otomatis dari Hasil TOPSIS")

        # Ranking Esai
        ranking_esai = {}

        for i, row in enumerate(
            esai_rank.itertuples(),
            start=1
        ):
            ranking_esai[row.id] = i


        # Ranking Wawancara
        ranking_wawancara = {}

        for i, row in enumerate(
            wawancara_rank.itertuples(),
            start=1
        ):
            ranking_wawancara[row.id] = i


        # Ranking Rencana Studi
        ranking_rencana = {}

        for i, row in enumerate(
            rencana_rank.itertuples(),
            start=1
        ):
            ranking_rencana[row.id] = i


        # Bobot tiap DM
        bobot_dm = {
            'esai': 0.40,
            'wawancara': 0.35,
            'rencana': 0.25
        }

        # Tampilkan ranking
        st.write("Ranking Esai")
        st.write(ranking_esai)

        st.write("Ranking Wawancara")
        st.write(ranking_wawancara)

        st.write("Ranking Rencana Studi")
        st.write(ranking_rencana)

        # =========================
        # WEIGHTED BORDA
        # =========================

        st.subheader("Hasil Weighted Borda")

        # Mengambil peserta
        peserta = list(
            set(ranking_esai.keys()) &
            set(ranking_wawancara.keys()) &
            set(ranking_rencana.keys())
        )

        # Jumlah peserta
        jumlah_peserta = len(peserta)

        # Final score
        final_score = {}

        # Perhitungan Weighted Borda
        for p in peserta:

            borda = (
                ((jumlah_peserta + 1 - ranking_esai[p]) * bobot_dm['esai']) +
                ((jumlah_peserta + 1 - ranking_wawancara[p]) * bobot_dm['wawancara']) +
                ((jumlah_peserta + 1 - ranking_rencana[p]) * bobot_dm['rencana'])
            )

            final_score[p] = borda


        # Final ranking
        final_rank = pd.DataFrame(
            list(final_score.items()),
            columns=['id', 'final_score']
        )

        final_rank = final_rank.sort_values(
            by='final_score',
            ascending=False
        )

        st.dataframe(final_rank)

        st.session_state['final_rank'] = final_rank

# =========================
# MENAMPILKAN HASIL TERSIMPAN
# =========================

if 'lolos_admin' in st.session_state:

    st.subheader("Peserta Lolos Administrasi")
    st.dataframe(st.session_state['lolos_admin'])


if 'bobot_esai' in st.session_state:

    st.subheader("Bobot AHP Esai")
    st.dataframe(st.session_state['bobot_esai'])


if 'bobot_wawancara' in st.session_state:

    st.subheader("Bobot AHP Wawancara")
    st.dataframe(st.session_state['bobot_wawancara'])


if 'bobot_rencana' in st.session_state:

    st.subheader("Bobot AHP Rencana Studi")
    st.dataframe(st.session_state['bobot_rencana'])


if 'esai_rank' in st.session_state:

    st.subheader("Ranking TOPSIS Esai")
    st.dataframe(st.session_state['esai_rank'])


if 'wawancara_rank' in st.session_state:

    st.subheader("Ranking TOPSIS Wawancara")
    st.dataframe(st.session_state['wawancara_rank'])


if 'rencana_rank' in st.session_state:

    st.subheader("Ranking TOPSIS Rencana Studi")
    st.dataframe(st.session_state['rencana_rank'])


# =========================
# VALIDASI FINAL
# =========================

if 'final_rank' in st.session_state:

    final_rank = st.session_state['final_rank']

    st.subheader("Validasi Akhir Kepala Puslapdik")

    # INPUT KUOTA
    kuota = st.number_input(
        "Masukkan Kuota Penerima :",
        min_value=1,
        value=2,
        step=1
    )

    # PENERIMA SEMENTARA
    st.subheader("Penerima Sementara")

    penerima_sementara = final_rank.head(kuota)

    st.dataframe(penerima_sementara)

    # INPUT BLACKLIST
    blacklist_input = st.text_input(
        "Masukkan ID peserta yang dibatalkan (pisahkan dengan koma jika lebih dari 1)",
        value=""
    )

    # Convert ke list
    blacklist = [
        x.strip()
        for x in blacklist_input.split(',')
        if x.strip() != ""
    ]

    # Info blacklist
    if len(blacklist) == 0:

        st.info("Tidak ada peserta yang dibatalkan")

    else:

        st.warning("Peserta yang dibatalkan:")

        st.write(blacklist)

    # VALIDASI FINAL
    final_validated = final_rank[
        ~final_rank['id'].isin(blacklist)
    ]

    # FINAL PENERIMA
    final_penerima = final_validated.head(kuota)

    st.subheader("Final Penerima Beasiswa")

    st.dataframe(final_penerima)

