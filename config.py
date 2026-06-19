import os
import hashlib
import random as _rnd
import pandas as pd

# ═══════════════════════════════════════════════════════════════
# KONFIGURASI PATH
# ═══════════════════════════════════════════════════════════════

BASE_DIR  = "data_beasiswa"
NILAI_DIR = f"{BASE_DIR}/penilaian"

def init_dirs():
    os.makedirs(BASE_DIR,  exist_ok=True)
    os.makedirs(NILAI_DIR, exist_ok=True)
    for folder in ["DM1_Esai", "DM2_RencanaStudi", "DM3_Wawancara"]:
        os.makedirs(f"{NILAI_DIR}/{folder}", exist_ok=True)

init_dirs()

# ═══════════════════════════════════════════════════════════════
# KONSTANTA SISTEM
# ═══════════════════════════════════════════════════════════════

BATAS_BAHASA      = {"ITP": 550, "PTE": 58, "IBT": 80, "IELTS": 6.5}
BATAS_IPK         = 3.00
BATAS_UKBI        = 578
BATAS_USIA_UMUM   = 32
BATAS_USIA_KULIAH = 33
KUOTA_BEASISWA    = 10

KRITERIA_DM = {
    "DM1_Esai": {
        "label":  "DM 1 — Esai",
        "folder": "DM1_Esai",
        "kriteria": [
            {"nama": "Relevansi_Topik",    "bobot": 0.25, "tipe": "benefit"},
            {"nama": "Kedalaman_Analisis", "bobot": 0.30, "tipe": "benefit"},
            {"nama": "Kualitas_Penulisan", "bobot": 0.25, "tipe": "benefit"},
            {"nama": "Orisinalitas_Ide",   "bobot": 0.20, "tipe": "benefit"},
        ],
    },
    "DM2_RencanaStudi": {
        "label":  "DM 2 — Rencana Studi",
        "folder": "DM2_RencanaStudi",
        "kriteria": [
            {"nama": "Kejelasan_Tujuan",   "bobot": 0.30, "tipe": "benefit"},
            {"nama": "Kelayakan_Timeline", "bobot": 0.25, "tipe": "benefit"},
            {"nama": "Relevansi_Bidang",   "bobot": 0.25, "tipe": "benefit"},
            {"nama": "Dampak_Rencana",     "bobot": 0.20, "tipe": "benefit"},
        ],
    },
    "DM3_Wawancara": {
        "label":  "DM 3 — Wawancara",
        "folder": "DM3_Wawancara",
        "kriteria": [
            {"nama": "Motivasi_Komitmen",    "bobot": 0.30, "tipe": "benefit"},
            {"nama": "Kemampuan_Komunikasi", "bobot": 0.25, "tipe": "benefit"},
            {"nama": "Pemahaman_Bidang",     "bobot": 0.25, "tipe": "benefit"},
            {"nama": "Leadership_Potential", "bobot": 0.20, "tipe": "benefit"},
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# AKUN INTERNAL (Admin, Kepala)
# ═══════════════════════════════════════════════════════════════

AKUN_INTERNAL = {
    "admin": {
        "role": "admin", "nama": "Tim Admin Puslapdik",
        "password_plain": "admin123", "info": {},
    },
    "kepala": {
        "role": "kepala", "nama": "Kepala Puslapdik",
        "password_plain": "kepala123", "info": {},
    },
}

# ═══════════════════════════════════════════════════════════════
# POOL ASESOR (10 per DM = 30 total)
# ═══════════════════════════════════════════════════════════════

ASESOR_POOL = [
    # ── DM1_Esai ──────────────────────────────────────────────
    {"asesor_id":"AS_DM1_01","username":"asesor_dm1_01","password_plain":"asesor123",
     "nama":"Dr. Budi Hartono",    "dm_key":"DM1_Esai","bidang":"Ilmu Komputer"},
    {"asesor_id":"AS_DM1_02","username":"asesor_dm1_02","password_plain":"asesor123",
     "nama":"Dr. Siti Rahayu",     "dm_key":"DM1_Esai","bidang":"Teknik Informatika"},
    {"asesor_id":"AS_DM1_03","username":"asesor_dm1_03","password_plain":"asesor123",
     "nama":"Dr. Eko Wahyudi",     "dm_key":"DM1_Esai","bidang":"Teknik Elektro"},
    {"asesor_id":"AS_DM1_04","username":"asesor_dm1_04","password_plain":"asesor123",
     "nama":"Dr. Putri Dewi",      "dm_key":"DM1_Esai","bidang":"Manajemen"},
    {"asesor_id":"AS_DM1_05","username":"asesor_dm1_05","password_plain":"asesor123",
     "nama":"Dr. Agus Santoso",    "dm_key":"DM1_Esai","bidang":"Psikologi"},
    {"asesor_id":"AS_DM1_06","username":"asesor_dm1_06","password_plain":"asesor123",
     "nama":"Dr. Rina Kusuma",     "dm_key":"DM1_Esai","bidang":"Hukum"},
    {"asesor_id":"AS_DM1_07","username":"asesor_dm1_07","password_plain":"asesor123",
     "nama":"Dr. Denny Prasetyo",  "dm_key":"DM1_Esai","bidang":"Kedokteran"},
    {"asesor_id":"AS_DM1_08","username":"asesor_dm1_08","password_plain":"asesor123",
     "nama":"Dr. Maya Indah",      "dm_key":"DM1_Esai","bidang":"Ekonomi"},
    {"asesor_id":"AS_DM1_09","username":"asesor_dm1_09","password_plain":"asesor123",
     "nama":"Dr. Hendra Gunawan",  "dm_key":"DM1_Esai","bidang":"Komunikasi"},
    {"asesor_id":"AS_DM1_10","username":"asesor_dm1_10","password_plain":"asesor123",
     "nama":"Dr. Lilis Suryani",   "dm_key":"DM1_Esai","bidang":"Teknik Sipil"},

    # ── DM2_RencanaStudi ──────────────────────────────────────
    {"asesor_id":"AS_DM2_01","username":"asesor_dm2_01","password_plain":"asesor123",
     "nama":"Dr. Fajar Nugroho",   "dm_key":"DM2_RencanaStudi","bidang":"Ilmu Komputer"},
    {"asesor_id":"AS_DM2_02","username":"asesor_dm2_02","password_plain":"asesor123",
     "nama":"Dr. Nurul Hidayah",   "dm_key":"DM2_RencanaStudi","bidang":"Teknik Informatika"},
    {"asesor_id":"AS_DM2_03","username":"asesor_dm2_03","password_plain":"asesor123",
     "nama":"Dr. Rudi Hartawan",   "dm_key":"DM2_RencanaStudi","bidang":"Teknik Elektro"},
    {"asesor_id":"AS_DM2_04","username":"asesor_dm2_04","password_plain":"asesor123",
     "nama":"Dr. Wulandari",       "dm_key":"DM2_RencanaStudi","bidang":"Manajemen"},
    {"asesor_id":"AS_DM2_05","username":"asesor_dm2_05","password_plain":"asesor123",
     "nama":"Dr. Surya Adi",       "dm_key":"DM2_RencanaStudi","bidang":"Psikologi"},
    {"asesor_id":"AS_DM2_06","username":"asesor_dm2_06","password_plain":"asesor123",
     "nama":"Dr. Laila Fitria",    "dm_key":"DM2_RencanaStudi","bidang":"Hukum"},
    {"asesor_id":"AS_DM2_07","username":"asesor_dm2_07","password_plain":"asesor123",
     "nama":"Dr. Bagas Prayogo",   "dm_key":"DM2_RencanaStudi","bidang":"Kedokteran"},
    {"asesor_id":"AS_DM2_08","username":"asesor_dm2_08","password_plain":"asesor123",
     "nama":"Dr. Indira Sari",     "dm_key":"DM2_RencanaStudi","bidang":"Ekonomi"},
    {"asesor_id":"AS_DM2_09","username":"asesor_dm2_09","password_plain":"asesor123",
     "nama":"Dr. Galuh Permata",   "dm_key":"DM2_RencanaStudi","bidang":"Komunikasi"},
    {"asesor_id":"AS_DM2_10","username":"asesor_dm2_10","password_plain":"asesor123",
     "nama":"Dr. Wahyu Setiawan",  "dm_key":"DM2_RencanaStudi","bidang":"Teknik Sipil"},

    # ── DM3_Wawancara ─────────────────────────────────────────
    {"asesor_id":"AS_DM3_01","username":"asesor_dm3_01","password_plain":"asesor123",
     "nama":"Dr. Citra Lestari",   "dm_key":"DM3_Wawancara","bidang":"Ilmu Komputer"},
    {"asesor_id":"AS_DM3_02","username":"asesor_dm3_02","password_plain":"asesor123",
     "nama":"Dr. Taufik Rahman",   "dm_key":"DM3_Wawancara","bidang":"Teknik Informatika"},
    {"asesor_id":"AS_DM3_03","username":"asesor_dm3_03","password_plain":"asesor123",
     "nama":"Dr. Yeni Susanti",    "dm_key":"DM3_Wawancara","bidang":"Teknik Elektro"},
    {"asesor_id":"AS_DM3_04","username":"asesor_dm3_04","password_plain":"asesor123",
     "nama":"Dr. Andi Wijaya",     "dm_key":"DM3_Wawancara","bidang":"Manajemen"},
    {"asesor_id":"AS_DM3_05","username":"asesor_dm3_05","password_plain":"asesor123",
     "nama":"Dr. Fitriani",        "dm_key":"DM3_Wawancara","bidang":"Psikologi"},
    {"asesor_id":"AS_DM3_06","username":"asesor_dm3_06","password_plain":"asesor123",
     "nama":"Dr. Reza Firmansyah", "dm_key":"DM3_Wawancara","bidang":"Hukum"},
    {"asesor_id":"AS_DM3_07","username":"asesor_dm3_07","password_plain":"asesor123",
     "nama":"Dr. Dewi Maharani",   "dm_key":"DM3_Wawancara","bidang":"Kedokteran"},
    {"asesor_id":"AS_DM3_08","username":"asesor_dm3_08","password_plain":"asesor123",
     "nama":"Dr. Gilang Saputra",  "dm_key":"DM3_Wawancara","bidang":"Ekonomi"},
    {"asesor_id":"AS_DM3_09","username":"asesor_dm3_09","password_plain":"asesor123",
     "nama":"Dr. Nadia Putri",     "dm_key":"DM3_Wawancara","bidang":"Komunikasi"},
    {"asesor_id":"AS_DM3_10","username":"asesor_dm3_10","password_plain":"asesor123",
     "nama":"Dr. Prio Handoko",    "dm_key":"DM3_Wawancara","bidang":"Teknik Sipil"},
]

# Index cepat: username → data asesor
ASESOR_BY_USERNAME = {a["username"]: a for a in ASESOR_POOL}
ASESOR_BY_ID       = {a["asesor_id"]: a for a in ASESOR_POOL}

# ═══════════════════════════════════════════════════════════════
# UTILITAS: HASHING
# ═══════════════════════════════════════════════════════════════

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# ═══════════════════════════════════════════════════════════════
# DATA DUMMY (definisi final yang dipakai sistem)
# ═══════════════════════════════════════════════════════════════

def _buat_kandidat():
    """
    Generate 50 kandidat dummy.
    SEMUA kandidat: formulir belum dikirim (pendaftaran_lengkap=False),
    dokumen kosong, status pending — kandidat harus submit sendiri.

    Data numerik sudah terisi sebagai nilai default di form:
      K001–K030 → data numerik BURUK (akan gagal auto-check saat submit)
      K031–K050 → data numerik BAGUS (akan lolos auto-check saat submit)
    """
    _rnd.seed(42)

    _nama_depan = [
        "Andi","Budi","Citra","Dian","Eko","Farah","Gilang","Hana","Ivan","Julia",
        "Kevin","Lina","Mario","Nina","Oscar","Putri","Qori","Reza","Sari","Tono",
        "Umar","Vina","Wahyu","Xena","Yudi","Zara","Agus","Bella","Cahya","Dedi",
        "Elsa","Fandi","Gita","Hadi","Irma","Joko","Kiki","Luki","Mira","Nanda",
    ]
    _nama_belakang = [
        "Pratama","Santoso","Dewi","Rahayu","Prasetyo","Nadia","Ramadhan","Kusuma",
        "Wijaya","Putri","Setiawan","Hartono","Nugroho","Sari","Hidayat","Wulandari",
        "Rahman","Fitria","Gunawan","Lestari","Firmansyah","Maharani","Saputra",
        "Permata","Handoko","Kurniawan","Suryani","Indah","Prayogo","Wahyudi",
    ]
    _univ  = ["UGM","UI","ITB","UNAIR","ITS","UNDIP","UB","UNPAD","USU","UNSRI"]
    _prodi = [
        "Ilmu Komputer","Teknik Informatika","Teknik Elektro","Manajemen",
        "Psikologi","Hukum","Kedokteran","Ekonomi","Komunikasi","Teknik Sipil",
    ]

    def _skor_bahasa_valid(jenis):
        return {"ITP":_rnd.randint(555,625),"PTE":_rnd.randint(60,80),
                "IBT":_rnd.randint(82,105),"IELTS":round(_rnd.uniform(6.5,8.5),1)}[jenis]

    hasil = []
    for i in range(1, 51):
        kid   = f"K{i:03d}"
        nama  = f"{_rnd.choice(_nama_depan)} {_rnd.choice(_nama_belakang)}"
        prodi = _prodi[(i - 1) % 10]
        jenis = _rnd.choice(["ITP","PTE","IBT","IELTS"])

        tgl = (f"2025-01-{_rnd.randint(10,28):02d} "
               f"{_rnd.randint(8,17):02d}:{_rnd.randint(0,59):02d}")

        # ── K001–K030: data numerik BURUK ──────────────────────
        if i <= 30:
            ipk      = round(_rnd.uniform(3.30, 3.95), 2)
            usia     = _rnd.randint(22, 28)
            ukbi     = _rnd.randint(582, 650)
            skor_tes = _skor_bahasa_valid(jenis)

            # Suntikkan kegagalan per kelompok
            if   1  <= i <= 7:   ipk      = round(_rnd.uniform(2.00, 2.99), 2)  # IPK kurang
            elif 8  <= i <= 14:  usia     = _rnd.randint(34, 45)                 # Usia lewat batas
            elif 15 <= i <= 21:  ukbi     = _rnd.randint(300, 577)               # UKBI kurang
            elif 22 <= i <= 26:
                jenis    = "ITP"
                skor_tes = _rnd.randint(300, 549)                                 # Skor bahasa kurang
            elif 27 <= i <= 30:  ipk      = round(_rnd.uniform(1.80, 2.49), 2)  # IPK sangat kurang

        # ── K031–K050: data numerik BAGUS ──────────────────────
        else:
            ipk      = round(_rnd.uniform(3.30, 3.95), 2)
            usia     = _rnd.randint(22, 28)
            ukbi     = _rnd.randint(582, 650)
            skor_tes = _skor_bahasa_valid(jenis)

        # Semua kandidat: formulir belum dikirim, dokumen kosong
        hasil.append({
            "id": kid, "nama": nama, "usia": usia, "sedang_kuliah": False,
            "universitas": _rnd.choice(_univ), "prodi": prodi, "ipk": ipk,
            "jenis_tes_bahasa": jenis, "skor_tes_bahasa": skor_tes,
            "skor_ukbi": ukbi,
            "file_rekomendasi":     "",
            "file_loa_surat_aktif": "",
            "file_rencana_studi":   "",
            "file_esai":            "",
            "esai_kata":            "",
            "tanggal_daftar":       tgl,
            "pendaftaran_lengkap":  False,  # belum submit — kandidat submit sendiri
        })

    return hasil

# Panggil sekali dan simpan ke konstanta
DUMMY_KANDIDAT = _buat_kandidat()

# ── Status verifikasi awal ──────────────────────────────────────
# Semua pending — status baru berubah setelah kandidat submit formulir
DUMMY_VERIFIKASI = {f"K{i:03d}": "pending" for i in range(1, 51)}

# ── Asesor assignment ───────────────────────────────────────────
DUMMY_ASSIGNMENTS = []

# ── Skor penilaian ─────────────────────────────────────────────
_rnd.seed(99)
def _skor(base, spread=8):
    return max(60, min(100, base + _rnd.randint(-spread, spread)))

DUMMY_SCORES = {}
