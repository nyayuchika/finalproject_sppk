import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="GDSS Beasiswa Unggulan S2",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# DATA DUMMY
# ═══════════════════════════════════════════════════════════════

KANDIDAT_DATA = [
    {"id": "K001", "nama": "Andi Pratama",    "universitas": "UGM",   "prodi": "Ilmu Komputer",     "ipk": 3.82, "usia": 24, "ukbi": 610, "eng_score": 570, "eng_type": "ITP",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1750},
    {"id": "K002", "nama": "Budi Santoso",    "universitas": "UI",    "prodi": "Teknik Informatika","ipk": 3.55, "usia": 27, "ukbi": 595, "eng_score":  62, "eng_type": "PTE",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1820},
    {"id": "K003", "nama": "Citra Dewi",      "universitas": "ITB",   "prodi": "Teknik Elektro",    "ipk": 3.91, "usia": 26, "ukbi": 625, "eng_score": 7.0, "eng_type": "IELTS", "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1950},
    {"id": "K004", "nama": "Dian Rahayu",     "universitas": "UGM",   "prodi": "Psikologi",         "ipk": 3.67, "usia": 25, "ukbi": 580, "eng_score": 555, "eng_type": "ITP",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1680},
    {"id": "K005", "nama": "Eko Prasetyo",    "universitas": "UNAIR", "prodi": "Manajemen",         "ipk": 3.45, "usia": 29, "ukbi": 590, "eng_score":  85, "eng_type": "IBT",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1550},
    {"id": "K006", "nama": "Farah Nadia",     "universitas": "UI",    "prodi": "Hukum",             "ipk": 3.78, "usia": 28, "ukbi": 615, "eng_score": 565, "eng_type": "ITP",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1900},
    {"id": "K007", "nama": "Gilang Ramadhan", "universitas": "ITS",   "prodi": "Teknik Sipil",      "ipk": 3.60, "usia": 26, "ukbi": 585, "eng_score": 560, "eng_type": "ITP",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1700},
    {"id": "K008", "nama": "Hana Kusuma",     "universitas": "UGM",   "prodi": "Kedokteran",        "ipk": 3.95, "usia": 25, "ukbi": 635, "eng_score": 8.0, "eng_type": "IELTS", "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1980},
    # Kandidat yang akan gagal administrasi (untuk demo)
    {"id": "K009", "nama": "Ivan Wijaya",     "universitas": "UGM",   "prodi": "Ekonomi",           "ipk": 2.95, "usia": 30, "ukbi": 580, "eng_score": 555, "eng_type": "ITP",   "rekomendasi": True,  "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1600},
    {"id": "K010", "nama": "Julia Putri",     "universitas": "UI",    "prodi": "Komunikasi",        "ipk": 3.50, "usia": 34, "ukbi": 570, "eng_score": 540, "eng_type": "ITP",   "rekomendasi": False, "loa": True,  "rencana_studi": True, "esai": True, "esai_kata": 1750},
]

DM_DATA = [
    {"id": "DM001", "nama": "Prof. Ahmad Yusuf",    "institusi": "UGM",   "bidang": "Ilmu Komputer", "kriteria": "esai"},
    {"id": "DM002", "nama": "Dr. Sari Indah",       "institusi": "UI",    "bidang": "Informatika",   "kriteria": "esai"},
    {"id": "DM003", "nama": "Prof. Bambang Heru",   "institusi": "ITB",   "bidang": "Teknik",        "kriteria": "rencana_studi"},
    {"id": "DM004", "nama": "Dr. Retno Wulandari",  "institusi": "UNAIR", "bidang": "Manajemen",     "kriteria": "rencana_studi"},
    {"id": "DM005", "nama": "Prof. Hendra Gunawan", "institusi": "UGM",   "bidang": "Psikologi",     "kriteria": "wawancara"},
    {"id": "DM006", "nama": "Dr. Maya Sari",        "institusi": "ITS",   "bidang": "Teknik",        "kriteria": "wawancara"},
]

SUBCRITERIA_WEIGHTS = {
    "esai": {
        "kesesuaian_tema":   0.35,
        "kejelasan_tujuan":  0.30,
        "dampak_kontribusi": 0.20,
        "orisinalitas":      0.15,
    },
    "rencana_studi": {
        "alasan_memilih_prodi": 0.40,
        "topik_tesis":          0.30,
        "timeline_studi":       0.30,
    },
    "wawancara": {
        "kesesuaian_esai":   0.30,
        "motivasi":          0.20,
        "critical_thinking": 0.20,
        "komunikasi":        0.15,
        "prestasi":          0.15,
    },
}

BORDA_WEIGHTS = {"wawancara": 0.50, "esai": 0.30, "rencana_studi": 0.20}

# K001–K006 sudah diverifikasi; K007–K010 pending untuk demo admin
INIT_VERIFICATIONS = {
    "K001": "lolos", "K002": "lolos", "K003": "lolos",
    "K004": "lolos", "K005": "lolos", "K006": "lolos",
    "K007": "pending", "K008": "pending",
    "K009": "pending", "K010": "pending",
}

# Skor sudah diisi untuk K001–K006 (K007 & K008 dikosongkan untuk demo DM)
# Distribusi round-robin: DM001→K001,K003,K005,K007 | DM002→K002,K004,K006,K008
PREFILLED_SCORES = {
    # ── DM001 (esai) ──────────────────────────────────────────────
    ("DM001","K001"): {"kesesuaian_tema":85,"kejelasan_tujuan":80,"dampak_kontribusi":75,"orisinalitas":70},
    ("DM001","K003"): {"kesesuaian_tema":90,"kejelasan_tujuan":88,"dampak_kontribusi":85,"orisinalitas":82},
    ("DM001","K005"): {"kesesuaian_tema":78,"kejelasan_tujuan":80,"dampak_kontribusi":74,"orisinalitas":72},
    # ── DM002 (esai) ──────────────────────────────────────────────
    ("DM002","K002"): {"kesesuaian_tema":70,"kejelasan_tujuan":75,"dampak_kontribusi":65,"orisinalitas":60},
    ("DM002","K004"): {"kesesuaian_tema":72,"kejelasan_tujuan":68,"dampak_kontribusi":70,"orisinalitas":65},
    ("DM002","K006"): {"kesesuaian_tema":82,"kejelasan_tujuan":85,"dampak_kontribusi":80,"orisinalitas":78},
    # ── DM003 (rencana_studi) ─────────────────────────────────────
    ("DM003","K001"): {"alasan_memilih_prodi":88,"topik_tesis":82,"timeline_studi":85},
    ("DM003","K003"): {"alasan_memilih_prodi":92,"topik_tesis":90,"timeline_studi":88},
    ("DM003","K005"): {"alasan_memilih_prodi":80,"topik_tesis":78,"timeline_studi":75},
    # ── DM004 (rencana_studi) ─────────────────────────────────────
    ("DM004","K002"): {"alasan_memilih_prodi":72,"topik_tesis":68,"timeline_studi":70},
    ("DM004","K004"): {"alasan_memilih_prodi":75,"topik_tesis":70,"timeline_studi":72},
    ("DM004","K006"): {"alasan_memilih_prodi":85,"topik_tesis":82,"timeline_studi":80},
    # ── DM005 (wawancara) ─────────────────────────────────────────
    ("DM005","K001"): {"kesesuaian_esai":82,"motivasi":88,"critical_thinking":80,"komunikasi":85,"prestasi":78},
    ("DM005","K003"): {"kesesuaian_esai":91,"motivasi":90,"critical_thinking":88,"komunikasi":87,"prestasi":85},
    ("DM005","K005"): {"kesesuaian_esai":78,"motivasi":80,"critical_thinking":76,"komunikasi":74,"prestasi":72},
    # ── DM006 (wawancara) ─────────────────────────────────────────
    ("DM006","K002"): {"kesesuaian_esai":70,"motivasi":75,"critical_thinking":68,"komunikasi":72,"prestasi":65},
    ("DM006","K004"): {"kesesuaian_esai":74,"motivasi":78,"critical_thinking":72,"komunikasi":75,"prestasi":70},
    ("DM006","K006"): {"kesesuaian_esai":84,"motivasi":82,"critical_thinking":80,"komunikasi":83,"prestasi":79},
    # K007 dan K008 SENGAJA dikosongkan → diisi saat demo DM
}

# Skor K007 & K008 yang akan dipakai saat tombol "Isi Demo Otomatis" ditekan
DEMO_SCORES_K007_K008 = {
    ("DM001","K007"): {"kesesuaian_tema":68,"kejelasan_tujuan":72,"dampak_kontribusi":65,"orisinalitas":60},
    ("DM002","K008"): {"kesesuaian_tema":88,"kejelasan_tujuan":86,"dampak_kontribusi":84,"orisinalitas":80},
    ("DM003","K007"): {"alasan_memilih_prodi":70,"topik_tesis":65,"timeline_studi":68},
    ("DM004","K008"): {"alasan_memilih_prodi":90,"topik_tesis":88,"timeline_studi":86},
    ("DM005","K007"): {"kesesuaian_esai":68,"motivasi":70,"critical_thinking":65,"komunikasi":67,"prestasi":63},
    ("DM006","K008"): {"kesesuaian_esai":90,"motivasi":88,"critical_thinking":86,"komunikasi":84,"prestasi":82},
}

# ═══════════════════════════════════════════════════════════════
# FUNGSI AUTO-CHECK ADMINISTRASI
# ═══════════════════════════════════════════════════════════════

def auto_check(k):
    """
    Cek otomatis persyaratan administrasi.
    Mengembalikan list tuple (level, pesan):
      level = 'error' | 'warning'
    """
    flags = []
    if k["ipk"] < 3.00:
        flags.append(("error", f"IPK {k['ipk']} di bawah batas minimal (3.00)"))
    if k["usia"] > 33:
        flags.append(("error", f"Usia {k['usia']} tahun melebihi batas maksimal (33 tahun)"))
    if not k["rekomendasi"]:
        flags.append(("error", "Surat rekomendasi tidak ditemukan"))
    if not k["loa"]:
        flags.append(("warning", "Surat LoA / surat aktif tidak ditemukan"))
    if not k["rencana_studi"]:
        flags.append(("error", "Dokumen rencana studi tidak ada"))
    if not k["esai"]:
        flags.append(("error", "Dokumen esai tidak ada"))
    if k["esai"] and not (1500 <= k["esai_kata"] <= 2000):
        flags.append(("error", f"Jumlah kata esai tidak sesuai ({k['esai_kata']} kata, harus 1500–2000)"))
    if k["ukbi"] < 578:
        flags.append(("error", f"Skor UKBI {k['ukbi']} tidak memenuhi syarat (minimal 578)"))
    eng_ok = (
        (k["eng_type"] == "ITP"   and k["eng_score"] >= 550) or
        (k["eng_type"] == "PTE"   and k["eng_score"] >= 58)  or
        (k["eng_type"] == "IBT"   and k["eng_score"] >= 80)  or
        (k["eng_type"] == "IELTS" and k["eng_score"] >= 6.5)
    )
    if not eng_ok:
        flags.append(("error", f"Skor {k['eng_type']} {k['eng_score']} tidak memenuhi syarat"))
    return flags

# ═══════════════════════════════════════════════════════════════
# ALGORITMA TOPSIS (Global — Opsi B)
# ═══════════════════════════════════════════════════════════════

def run_topsis(scores_dict, weights):
    """
    Menjalankan TOPSIS secara global untuk satu kriteria.

    Parameter:
      scores_dict : {kandidat_id: {subkriteria: nilai (0-100)}}
      weights     : {subkriteria: bobot}

    Return:
      {kandidat_id: closeness_coefficient}
    """
    if not scores_dict:
        return {}

    ids = list(scores_dict.keys())
    sks = list(weights.keys())

    # 1. Bangun matriks keputusan (n kandidat × m subkriteria)
    matrix = np.array(
        [[scores_dict[kid][sk] for sk in sks] for kid in ids],
        dtype=float
    )

    # 2. Normalisasi matriks (normalisasi vektor)
    col_norms = np.sqrt((matrix ** 2).sum(axis=0))
    col_norms[col_norms == 0] = 1          # hindari bagi nol
    norm_matrix = matrix / col_norms

    # 3. Matriks terbobot
    w = np.array([weights[sk] for sk in sks])
    weighted = norm_matrix * w

    # 4. Solusi ideal positif (A+) dan negatif (A-)
    #    Semua subkriteria dianggap benefit (semakin tinggi semakin baik)
    ideal_pos = weighted.max(axis=0)
    ideal_neg = weighted.min(axis=0)

    # 5. Hitung jarak Euclidean ke A+ dan A-
    d_pos = np.sqrt(((weighted - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_neg) ** 2).sum(axis=1))

    # 6. Closeness Coefficient (CC) — semakin mendekati 1 semakin baik
    cc = d_neg / (d_pos + d_neg + 1e-10)

    return {kid: round(float(cc[i]), 4) for i, kid in enumerate(ids)}

# ═══════════════════════════════════════════════════════════════
# ALGORITMA WEIGHTED BORDA COUNT
# ═══════════════════════════════════════════════════════════════

def run_borda(rankings_dict, weights):
    """
    Menggabungkan ranking dari beberapa kriteria menggunakan Weighted Borda.

    Parameter:
      rankings_dict : {kriteria: {kandidat_id: rank}} — rank 1 = terbaik
      weights       : {kriteria: bobot}

    Return:
      [(kandidat_id, borda_score)] diurutkan descending
    """
    all_ids = set()
    for r in rankings_dict.values():
        all_ids.update(r.keys())
    n = len(all_ids)

    borda_scores = {kid: 0.0 for kid in all_ids}
    for kriteria, ranking in rankings_dict.items():
        w = weights[kriteria]
        for kid, rank in ranking.items():
            borda_pts = n - rank        # rank 1 → (n-1) poin, rank n → 0 poin
            borda_scores[kid] += w * borda_pts

    return sorted(borda_scores.items(), key=lambda x: x[1], reverse=True)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE & DISTRIBUSI
# ═══════════════════════════════════════════════════════════════

def init_state():
    if "ready" in st.session_state:
        return
    st.session_state.ready          = True
    st.session_state.logged_in      = False
    st.session_state.role           = None
    st.session_state.user           = None
    st.session_state.verifications  = dict(INIT_VERIFICATIONS)
    st.session_state.admin_closed   = False
    st.session_state.assignments    = {}          # dm_id → [kid]
    st.session_state.scores         = dict(PREFILLED_SCORES)
    st.session_state.topsis_results = {}
    st.session_state.final_ranking  = []
    st.session_state.borda_done     = False


def distribute_candidates():
    """
    Distribusi round-robin kandidat lolos ke DM per kriteria.
    Dipanggil saat Admin menutup tahap administrasi.
    """
    lolos = [k["id"] for k in KANDIDAT_DATA
             if st.session_state.verifications.get(k["id"]) == "lolos"]

    dm_by_kriteria = {}
    for dm in DM_DATA:
        dm_by_kriteria.setdefault(dm["kriteria"], []).append(dm["id"])

    assignments = {dm["id"]: [] for dm in DM_DATA}
    for kriteria, dm_ids in dm_by_kriteria.items():
        for i, kid in enumerate(lolos):
            dm_id = dm_ids[i % len(dm_ids)]
            assignments[dm_id].append(kid)

    st.session_state.assignments = assignments

# ═══════════════════════════════════════════════════════════════
# HELPER UMUM
# ═══════════════════════════════════════════════════════════════

def get_kandidat(kid):
    return next((k for k in KANDIDAT_DATA if k["id"] == kid), None)

def get_dm(dm_id):
    return next((d for d in DM_DATA if d["id"] == dm_id), None)

def status_badge(status):
    icons  = {"lolos": "🟢", "tidak_lolos": "🔴", "pending": "🟡"}
    labels = {"lolos": "Lolos", "tidak_lolos": "Tidak Lolos", "pending": "Pending"}
    return f"{icons.get(status,'⚪')} {labels.get(status,'—')}"

def dm_progress(dm_id, kriteria):
    """Menghitung berapa kandidat sudah dinilai oleh DM tertentu."""
    sks      = list(SUBCRITERIA_WEIGHTS[kriteria].keys())
    assigned = st.session_state.assignments.get(dm_id, [])
    done     = sum(
        1 for kid in assigned
        if all(sk in st.session_state.scores.get((dm_id, kid), {}) for sk in sks)
    )
    return done, len(assigned)

def all_dms_done():
    for dm in DM_DATA:
        done, total = dm_progress(dm["id"], dm["kriteria"])
        if done < total:
            return False
    return True

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎓 GDSS Beasiswa Unggulan S2")
        st.markdown("---")
        role_label = {
            "kandidat": "👤 Kandidat",
            "admin":    "🛡️ Admin",
            "dm":       "📊 Decision Maker",
            "kepala":   "👑 Kepala Puslapdik",
        }
        st.markdown(f"**{st.session_state.user.get('nama', '—')}**")
        st.caption(role_label.get(st.session_state.role, ""))
        st.markdown("---")

        # Ringkasan status sistem
        n_lolos   = sum(1 for v in st.session_state.verifications.values() if v == "lolos")
        n_pending = sum(1 for v in st.session_state.verifications.values() if v == "pending")
        st.caption("**Status Sistem**")
        st.caption(f"Administrasi: {'✅ Ditutup' if st.session_state.admin_closed else '🔓 Terbuka'}")
        st.caption(f"Kandidat lolos: {n_lolos} | Pending: {n_pending}")
        st.caption(f"Hasil final: {'✅ Ada' if st.session_state.borda_done else '⏳ Belum'}")
        st.markdown("---")

        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role      = None
            st.session_state.user      = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# HALAMAN: LOGIN
# ═══════════════════════════════════════════════════════════════

def page_login():
    st.markdown(
        "<h1 style='text-align:center; padding-top:2rem'>🎓 GDSS Seleksi Beasiswa Unggulan S2</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; color:gray'>Group Decision Support System — Puslapdik Kemdikbud</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.subheader("Masuk ke Sistem")
        role = st.selectbox("Login sebagai:", [
            "— Pilih Role —", "Kandidat", "Admin", "Decision Maker", "Kepala Puslapdik"
        ])

        if role == "Kandidat":
            opts = {f"{k['nama']} ({k['id']})": k["id"] for k in KANDIDAT_DATA[:4]}
            sel  = st.selectbox("Pilih akun (demo):", list(opts.keys()))
            if st.button("Masuk", use_container_width=True, type="primary"):
                kid = opts[sel]
                k   = get_kandidat(kid)
                st.session_state.logged_in = True
                st.session_state.role      = "kandidat"
                st.session_state.user      = {"nama": k["nama"], "kid": kid}
                st.rerun()

        elif role == "Admin":
            if st.button("Masuk sebagai Admin", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.session_state.role      = "admin"
                st.session_state.user      = {"nama": "Tim Admin Puslapdik"}
                st.rerun()

        elif role == "Decision Maker":
            opts = {
                f"{dm['nama']} — {dm['kriteria'].replace('_',' ').title()} ({dm['id']})": dm["id"]
                for dm in DM_DATA
            }
            sel = st.selectbox("Pilih akun DM (demo):", list(opts.keys()))
            if st.button("Masuk sebagai Decision Maker", use_container_width=True, type="primary"):
                dm_id = opts[sel]
                st.session_state.logged_in = True
                st.session_state.role      = "dm"
                st.session_state.user      = get_dm(dm_id)
                st.rerun()

        elif role == "Kepala Puslapdik":
            if st.button("Masuk sebagai Kepala Puslapdik", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.session_state.role      = "kepala"
                st.session_state.user      = {"nama": "Kepala Puslapdik"}
                st.rerun()

        if role != "— Pilih Role —":
            st.info("ℹ️ Sistem demo — tidak ada autentikasi nyata.")

# ═══════════════════════════════════════════════════════════════
# HALAMAN: KANDIDAT
# ═══════════════════════════════════════════════════════════════

def page_kandidat():
    render_sidebar()
    kid    = st.session_state.user["kid"]
    k      = get_kandidat(kid)
    status = st.session_state.verifications.get(kid, "pending")

    st.title("👤 Dashboard Kandidat")
    st.markdown(f"Selamat datang, **{k['nama']}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Universitas Tujuan", k["universitas"])
    c2.metric("Program Studi",      k["prodi"])
    c3.metric("IPK",                k["ipk"])
    c4.metric("Usia",               f"{k['usia']} thn")

    st.markdown("---")
    st.subheader("📋 Status Aplikasi")

    steps = [
        ("📝 Pendaftaran",             "Selesai",                                      True),
        ("🔍 Verifikasi Administrasi",
            "Lolos ✅" if status == "lolos" else
            ("Tidak Lolos ❌" if status == "tidak_lolos" else "Sedang Diproses ⏳"),
            status in ["lolos", "tidak_lolos"]),
        ("📊 Penilaian Substansi",
            "Sedang Dinilai ⏳" if (status == "lolos" and st.session_state.admin_closed) else
            ("Tidak Berlanjut" if status == "tidak_lolos" else "Menunggu ⏳"),
            st.session_state.borda_done and status == "lolos"),
        ("🏆 Hasil Final",
            "Tersedia ✅" if st.session_state.borda_done else "Menunggu ⏳",
            st.session_state.borda_done),
    ]

    for label, val, done in steps:
        ca, cb = st.columns([5, 1])
        with ca:
            st.markdown(f"**{label}**")
            st.caption(val)
        with cb:
            st.markdown("### ✅" if done else "### ⏳")
        st.markdown("---")

    if st.session_state.borda_done and status == "lolos":
        ids = [kid_ for kid_, _ in st.session_state.final_ranking]
        if kid in ids:
            rank  = ids.index(kid) + 1
            total = len(ids)
            st.success(f"🏆 Peringkat Akhir Anda: **#{rank}** dari {total} kandidat substansi")

# ═══════════════════════════════════════════════════════════════
# HALAMAN: ADMIN
# ═══════════════════════════════════════════════════════════════

def page_admin():
    render_sidebar()
    st.title("🛡️ Dashboard Admin")

    tab1, tab2, tab3 = st.tabs(["📋 Verifikasi Kandidat", "👥 Decision Maker", "⚙️ Status Sistem"])

    # ── Tab 1 ──────────────────────────────────────────────────
    with tab1:
        n_lolos   = sum(1 for k in KANDIDAT_DATA if st.session_state.verifications.get(k["id"]) == "lolos")
        n_tolak   = sum(1 for k in KANDIDAT_DATA if st.session_state.verifications.get(k["id"]) == "tidak_lolos")
        n_pending = len(KANDIDAT_DATA) - n_lolos - n_tolak

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Kandidat", len(KANDIDAT_DATA))
        c2.metric("✅ Lolos",        n_lolos)
        c3.metric("❌ Tidak Lolos",  n_tolak)
        c4.metric("⏳ Pending",      n_pending)
        st.markdown("---")

        for k in KANDIDAT_DATA:
            flags  = auto_check(k)
            status = st.session_state.verifications.get(k["id"], "pending")
            has_err = any(f[0] == "error" for f in flags)

            icon = "✅" if status == "lolos" else (
                   "❌" if status == "tidak_lolos" else (
                   "⚠️" if flags else "⏳"))

            with st.expander(
                f"{icon} **{k['id']}** — {k['nama']}  |  {k['prodi']}, {k['universitas']}  |  {status_badge(status)}"
            ):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**IPK:** {k['ipk']}  \n**Usia:** {k['usia']} thn")
                c2.markdown(f"**UKBI:** {k['ukbi']}  \n**Bahasa:** {k['eng_type']} {k['eng_score']}")
                c3.markdown(f"**Kata Esai:** {k['esai_kata']}  \n**LoA:** {'✅' if k['loa'] else '❌'}  **Rekomen:** {'✅' if k['rekomendasi'] else '❌'}")

                if flags:
                    for ftype, fmsg in flags:
                        (st.error if ftype == "error" else st.warning)(f"{'❌' if ftype=='error' else '⚠️'} {fmsg}")
                else:
                    st.success("✅ Semua persyaratan terdeteksi terpenuhi oleh sistem")

                if not st.session_state.admin_closed:
                    ca, cb = st.columns(2)
                    with ca:
                        if st.button("✅ Loloskan", key=f"ok_{k['id']}", use_container_width=True):
                            st.session_state.verifications[k["id"]] = "lolos"
                            st.rerun()
                    with cb:
                        if st.button("❌ Tolak", key=f"no_{k['id']}", use_container_width=True):
                            st.session_state.verifications[k["id"]] = "tidak_lolos"
                            st.rerun()
                else:
                    st.info(f"Tahap administrasi sudah ditutup. Status akhir: **{status_badge(status)}**")

    # ── Tab 2 ──────────────────────────────────────────────────
    with tab2:
        st.subheader("Decision Maker Terdaftar")
        st.caption("Semua DM berikut sudah self-register dan disetujui Admin.")
        for dm in DM_DATA:
            krit = dm["kriteria"].replace("_", " ").title()
            st.markdown(f"**{dm['nama']}** `{dm['id']}`")
            st.caption(f"🏫 {dm['institusi']}  |  📚 {dm['bidang']}  |  🗂️ Kriteria: **{krit}**")
            st.markdown("---")

    # ── Tab 3 ──────────────────────────────────────────────────
    with tab3:
        st.subheader("Penutupan Tahap Administrasi")

        n_lolos   = sum(1 for k in KANDIDAT_DATA if st.session_state.verifications.get(k["id"]) == "lolos")
        n_pending = sum(1 for k in KANDIDAT_DATA if st.session_state.verifications.get(k["id"]) == "pending")

        if not st.session_state.admin_closed:
            if n_pending > 0:
                st.warning(f"⏳ Masih ada **{n_pending} kandidat** yang belum diverifikasi.")
            else:
                st.success("✅ Semua kandidat sudah diverifikasi. Siap menutup tahap administrasi.")

            if st.button(
                "🔒 Tutup Tahap Administrasi & Distribusikan Kandidat ke DM",
                type="primary", disabled=(n_pending > 0), use_container_width=True
            ):
                st.session_state.admin_closed = True
                distribute_candidates()
                st.success(f"✅ Ditutup! **{n_lolos} kandidat** didistribusikan ke Decision Maker.")
                st.rerun()
            if n_pending > 0:
                st.caption("Tombol aktif setelah semua kandidat selesai diverifikasi.")
        else:
            st.success(f"✅ Tahap administrasi sudah ditutup. **{n_lolos} kandidat lolos** telah didistribusikan.")
            st.subheader("Distribusi per Decision Maker")
            for dm in DM_DATA:
                assigned = st.session_state.assignments.get(dm["id"], [])
                names    = [get_kandidat(kid)["nama"] for kid in assigned]
                krit     = dm["kriteria"].replace("_", " ").title()
                st.markdown(f"**{dm['nama']}** ({krit}) → {len(assigned)} kandidat: {', '.join(names) if names else '—'}")

# ═══════════════════════════════════════════════════════════════
# HALAMAN: DECISION MAKER
# ═══════════════════════════════════════════════════════════════

def page_dm():
    render_sidebar()
    dm       = st.session_state.user
    dm_id    = dm["id"]
    kriteria = dm["kriteria"]
    weights  = SUBCRITERIA_WEIGHTS[kriteria]
    sks      = list(weights.keys())

    st.title("📊 Dashboard Decision Maker")
    st.markdown(f"**{dm['nama']}**  |  {dm['institusi']}  |  Kriteria: **{kriteria.replace('_',' ').title()}**")

    if not st.session_state.admin_closed:
        st.warning("⏳ Tahap administrasi belum ditutup oleh Admin. Kandidat belum dapat dinilai.")
        return

    assigned = st.session_state.assignments.get(dm_id, [])
    if not assigned:
        st.info("Tidak ada kandidat yang diassign ke Anda.")
        return

    done, total = dm_progress(dm_id, kriteria)
    st.progress(done / total if total else 0, text=f"Progress penilaian: {done}/{total} kandidat selesai")
    st.markdown("---")

    with st.expander("ℹ️ Panduan Subkriteria & Bobot"):
        for sk, w in weights.items():
            st.markdown(f"- **{sk.replace('_',' ').title()}**: bobot {w*100:.0f}%")
        st.caption("Input nilai 0–100 per subkriteria. TOPSIS akan dijalankan secara global oleh sistem.")

    st.subheader("📝 Input Penilaian Kandidat")

    for kid in assigned:
        k        = get_kandidat(kid)
        existing = st.session_state.scores.get((dm_id, kid), {})
        is_done  = all(sk in existing for sk in sks)

        with st.expander(
            f"{'✅' if is_done else '📝'} **{kid}** — {k['nama']}  |  {k['prodi']}, {k['universitas']}"
        ):
            st.caption(f"IPK: {k['ipk']}  |  Usia: {k['usia']} thn  |  {k['eng_type']}: {k['eng_score']}")
            st.caption("Berikan nilai 0–100 untuk setiap subkriteria di bawah ini.")

            cols       = st.columns(len(sks))
            new_scores = {}
            for i, sk in enumerate(sks):
                with cols[i]:
                    new_scores[sk] = st.number_input(
                        sk.replace("_", " ").title(),
                        min_value=0, max_value=100,
                        value=int(existing.get(sk, 70)),
                        step=1,
                        key=f"sc_{dm_id}_{kid}_{sk}"
                    )

            if st.button(f"💾 Simpan Penilaian {kid}", key=f"save_{dm_id}_{kid}", use_container_width=True):
                st.session_state.scores[(dm_id, kid)] = new_scores
                st.success(f"✅ Penilaian untuk **{k['nama']}** tersimpan!")
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# HALAMAN: KEPALA PUSLAPDIK
# ═══════════════════════════════════════════════════════════════

def page_kepala():
    render_sidebar()
    st.title("👑 Dashboard Kepala Puslapdik")

    tab1, tab2, tab3 = st.tabs(["⚙️ Bobot & Konfigurasi", "🚀 Jalankan Perhitungan", "🏆 Ranking Final"])

    # ── Tab 1: Bobot ───────────────────────────────────────────
    with tab1:
        st.subheader("Bobot Subkriteria per Kriteria (Fixed)")
        for kriteria, weights in SUBCRITERIA_WEIGHTS.items():
            st.markdown(f"##### {kriteria.replace('_',' ').title()}")
            df = pd.DataFrame({
                "Subkriteria": [s.replace("_", " ").title() for s in weights],
                "Bobot":       [f"{v*100:.0f}%" for v in weights.values()],
            })
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Bobot Borda (Antar Kriteria)")
        df_b = pd.DataFrame({
            "Kriteria": ["Wawancara", "Esai", "Rencana Studi"],
            "Bobot":    ["50%", "30%", "20%"],
        })
        st.dataframe(df_b, use_container_width=True, hide_index=True)
        st.caption("Bobot ditetapkan berdasarkan pedoman seleksi Beasiswa Unggulan S2.")

    # ── Tab 2: Jalankan ────────────────────────────────────────
    with tab2:
        st.subheader("Status Penilaian Decision Maker")

        if not st.session_state.admin_closed:
            st.warning("⏳ Tahap administrasi belum ditutup oleh Admin.")
            return

        for dm in DM_DATA:
            done, total = dm_progress(dm["id"], dm["kriteria"])
            krit        = dm["kriteria"].replace("_", " ").title()
            icon        = "✅" if done == total else "⏳"
            st.markdown(f"{icon} **{dm['nama']}** ({krit}) — {done}/{total} kandidat dinilai")

        st.markdown("---")

        # Tombol isi demo otomatis (untuk kemudahan presentasi)
        with st.expander("🛠️ Utilitas Demo"):
            st.caption("Gunakan tombol ini saat presentasi untuk mengisi skor K007 & K008 secara otomatis, sehingga perhitungan bisa langsung dijalankan.")
            if st.button("⚡ Isi Skor Demo Otomatis (K007 & K008)", use_container_width=True):
                st.session_state.scores.update(DEMO_SCORES_K007_K008)
                st.success("✅ Skor demo K007 & K008 berhasil diisi untuk semua kriteria!")
                st.rerun()

        can_run = all_dms_done()
        if not can_run:
            st.warning("⏳ Masih ada DM yang belum menyelesaikan penilaian. Selesaikan dulu atau gunakan utilitas demo di atas.")

        if st.button(
            "🚀 Jalankan TOPSIS Global + Weighted Borda",
            type="primary", use_container_width=True, disabled=not can_run
        ):
            # ── TOPSIS per kriteria ──
            with st.spinner("Menghitung TOPSIS global per kriteria..."):
                topsis_results = {}
                for kriteria in ["esai", "rencana_studi", "wawancara"]:
                    dms_k   = [dm for dm in DM_DATA if dm["kriteria"] == kriteria]
                    weights = SUBCRITERIA_WEIGHTS[kriteria]

                    all_scores = {}
                    for dm in dms_k:
                        for kid in st.session_state.assignments.get(dm["id"], []):
                            s = st.session_state.scores.get((dm["id"], kid))
                            if s:
                                all_scores[kid] = s

                    if all_scores:
                        cc          = run_topsis(all_scores, weights)
                        sorted_cc   = sorted(cc.items(), key=lambda x: x[1], reverse=True)
                        rankings    = {kid: rank + 1 for rank, (kid, _) in enumerate(sorted_cc)}
                        topsis_results[kriteria] = {"cc": cc, "ranking": rankings}

                st.session_state.topsis_results = topsis_results

            # ── Weighted Borda ──
            with st.spinner("Menggabungkan ranking dengan Weighted Borda..."):
                rankings_for_borda      = {k: v["ranking"] for k, v in topsis_results.items()}
                st.session_state.final_ranking = run_borda(rankings_for_borda, BORDA_WEIGHTS)
                st.session_state.borda_done    = True

            st.success("✅ Perhitungan selesai! Lihat hasil di tab **Ranking Final**.")
            st.rerun()

    # ── Tab 3: Hasil ───────────────────────────────────────────
    with tab3:
        st.subheader("🏆 Ranking Final Kandidat")

        if not st.session_state.borda_done:
            st.info("Belum ada hasil. Jalankan perhitungan di tab **Jalankan Perhitungan**.")
            return

        # Detail TOPSIS
        with st.expander("📊 Detail Hasil TOPSIS per Kriteria"):
            for kriteria, result in st.session_state.topsis_results.items():
                st.markdown(f"##### {kriteria.replace('_',' ').title()}")
                rows = []
                for kid, rank in sorted(result["ranking"].items(), key=lambda x: x[1]):
                    k = get_kandidat(kid)
                    rows.append({
                        "Rank": rank,
                        "ID":   kid,
                        "Nama": k["nama"],
                        "Closeness Coefficient (CC)": f"{result['cc'][kid]:.4f}",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Hasil Akhir — Weighted Borda Count")
        st.caption("Wawancara 50% + Esai 30% + Rencana Studi 20%")

        rows = []
        for rank, (kid, borda_score) in enumerate(st.session_state.final_ranking, 1):
            k = get_kandidat(kid)
            rows.append({
                "Peringkat":     f"#{rank}",
                "ID":            kid,
                "Nama":          k["nama"],
                "Universitas":   k["universitas"],
                "Program Studi": k["prodi"],
                "Borda Score":   f"{borda_score:.4f}",
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(
            "⚠️ Ranking ini adalah rekomendasi sistem. "
            "Penyesuaian kuota per universitas dapat dilakukan secara manual oleh Kepala Puslapdik."
        )

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    init_state()
    if not st.session_state.logged_in:
        page_login()
        return

    role = st.session_state.role
    if role == "kandidat":
        page_kandidat()
    elif role == "admin":
        page_admin()
    elif role == "dm":
        page_dm()
    elif role == "kepala":
        page_kepala()

if __name__ == "__main__":
    main()
