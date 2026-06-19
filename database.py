import os
import pandas as pd
from config import (BASE_DIR, NILAI_DIR, KRITERIA_DM,
                    DUMMY_KANDIDAT, DUMMY_VERIFIKASI, DUMMY_SCORES,
                    hash_pw)

# ═══════════════════════════════════════════════════════════════
# FILE I/O
# ═══════════════════════════════════════════════════════════════

def load_pendaftar() -> list:
    path = f"{BASE_DIR}/data_pendaftar.csv"
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return pd.read_csv(path).to_dict("records")
    except (pd.errors.EmptyDataError, Exception):
        pass
    return []

def save_pendaftar(records: list):
    pd.DataFrame(records).to_csv(f"{BASE_DIR}/data_pendaftar.csv", index=False)

def load_verifications() -> dict:
    path = f"{BASE_DIR}/verifikasi_admin.csv"
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            df = pd.read_csv(path)
            if not df.empty and "id" in df.columns:
                return dict(zip(df["id"].astype(str), df["status"]))
    except (pd.errors.EmptyDataError, Exception):
        pass
    return {}

def save_verifications(verif: dict):
    pd.DataFrame([{"id": k, "status": v} for k, v in verif.items()]).to_csv(
        f"{BASE_DIR}/verifikasi_admin.csv", index=False
    )

def load_akun_kandidat() -> pd.DataFrame:
    path = f"{BASE_DIR}/akun_kandidat.csv"
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return pd.read_csv(path)
    except (pd.errors.EmptyDataError, Exception):
        pass
    return pd.DataFrame(columns=["username", "password_hash", "kandidat_id"])

def save_akun_kandidat(df: pd.DataFrame):
    df.to_csv(f"{BASE_DIR}/akun_kandidat.csv", index=False)

def load_admin_closed() -> bool:
    """Baca status admin_closed dari file. True = tahap sudah ditutup."""
    return os.path.exists(f"{BASE_DIR}/admin_closed.txt")
 
def save_admin_closed():
    """Tandai bahwa admin sudah menutup tahap administrasi."""
    with open(f"{BASE_DIR}/admin_closed.txt", "w") as f:
        f.write("1")
 
def reset_admin_closed():
    """Hapus tanda admin_closed (untuk keperluan reset/testing)."""
    path = f"{BASE_DIR}/admin_closed.txt"
    if os.path.exists(path):
        os.remove(path)

def load_substansi_closed() -> bool:
    """True = perhitungan substansi sudah dijalankan dan dikunci."""
    return os.path.exists(f"{BASE_DIR}/substansi_closed.txt")

def save_substansi_closed():
    """Kunci tahap substansi setelah perhitungan TOPSIS+Borda selesai."""
    with open(f"{BASE_DIR}/substansi_closed.txt", "w") as f:
        f.write("1")

def load_penetapan_final() -> bool:
    """True = penetapan final sudah dilakukan dan dikunci."""
    return os.path.exists(f"{BASE_DIR}/penetapan_final.txt")

def save_penetapan_final():
    """Kunci tahap penetapan final setelah kepala menetapkan penerima."""
    with open(f"{BASE_DIR}/penetapan_final.txt", "w") as f:
        f.write("1")

def load_asesor_assignments() -> pd.DataFrame:
    path = f"{BASE_DIR}/asesor_assignments.csv"
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            df = pd.read_csv(path)
            if df.empty or len(df.columns) == 0:
                return pd.DataFrame(columns=["asesor_id", "kandidat_id", "dm_key", "status"])
            df["kandidat_id"] = df["kandidat_id"].astype(str)
            return df
    except (pd.errors.EmptyDataError, Exception):
        pass
    return pd.DataFrame(columns=["asesor_id", "kandidat_id", "dm_key", "status"])

def save_asesor_assignments(df: pd.DataFrame):
    df.to_csv(f"{BASE_DIR}/asesor_assignments.csv", index=False)

def load_scores_kandidat(dm_key: str, kid: str) -> dict:
    dm_info = KRITERIA_DM[dm_key]
    dm_dir  = f"{NILAI_DIR}/{dm_info['folder']}"
    hasil   = {}
    for k in dm_info["kriteria"]:
        path = f"{dm_dir}/{k['nama']}.csv"
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, index_col="id")
            df.index = df.index.astype(str)
            if str(kid) in df.index and "nilai" in df.columns:
                val = df.loc[str(kid), "nilai"]
                if not pd.isna(val):
                    hasil[k["nama"]] = float(val)
        except (pd.errors.EmptyDataError, Exception):
            continue
    return hasil

def load_scores_all_dm(dm_key: str, ids_lolos: list) -> pd.DataFrame:
    dm_info  = KRITERIA_DM[dm_key]
    dm_dir   = f"{NILAI_DIR}/{dm_info['folder']}"
    df_hasil = pd.DataFrame(index=[str(i) for i in ids_lolos])
    df_hasil.index.name = "id"

    for k in dm_info["kriteria"]:
        path = f"{dm_dir}/{k['nama']}.csv"
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, index_col="id")
            df.index = df.index.astype(str)
            df = df[df.index.isin(df_hasil.index)]
            if "nilai" in df.columns:
                df_hasil.loc[df.index, k["nama"]] = df["nilai"]
        except (pd.errors.EmptyDataError, Exception):
            continue

    return df_hasil.dropna(how="all")


def save_score(dm_key: str, kid: str, subkrit: str, nilai: float):
    """
    Simpan nilai satu kandidat untuk satu subkriteria.
    Format CSV: id, nilai  (1 baris per kandidat)
    """
    dm_info = KRITERIA_DM[dm_key]
    path    = f"{NILAI_DIR}/{dm_info['folder']}/{subkrit}.csv"

    if os.path.exists(path) and os.path.getsize(path) > 0:
        df = pd.read_csv(path, index_col="id")
        df.index = df.index.astype(str)
    else:
        df = pd.DataFrame(columns=["nilai"])
        df.index.name = "id"

    df.loc[str(kid), "nilai"] = nilai
    df.to_csv(path)

def seed_dummy_data():
    """
    Seed data awal hanya jika file belum ada.
    Tidak menimpa data yang sudah ada.
 
    Yang di-seed:
      data_pendaftar.csv   → 100 kandidat
      verifikasi_admin.csv → semua PENDING (admin verifikasi manual)
      akun_kandidat.csv    → login K001-K100 (password: kandidat123)
      penilaian/*/**.csv   → skor K001-K008 (siap dipakai setelah admin
                             loloskan mereka & tutup tahap)
 
    Yang TIDAK di-seed (dibuat saat runtime):
      asesor_assignments.csv → dibuat saat admin klik "Tutup Administrasi"
      admin_closed.txt       → dibuat saat admin klik "Tutup Administrasi"
      laporan_*.csv          → dibuat saat Kepala jalankan perhitungan
    """
    # 1. Kandidat
    path_k = f"{BASE_DIR}/data_pendaftar.csv"
    if not os.path.exists(path_k) or os.path.getsize(path_k) == 0:
        pd.DataFrame(DUMMY_KANDIDAT).to_csv(path_k, index=False)
 
    # 2. Verifikasi — semua pending
    path_v = f"{BASE_DIR}/verifikasi_admin.csv"
    if not os.path.exists(path_v) or os.path.getsize(path_v) == 0:
        pd.DataFrame([{"id": k, "status": v}
                      for k, v in DUMMY_VERIFIKASI.items()]).to_csv(path_v, index=False)
 
    # 3. Akun login kandidat
    path_a = f"{BASE_DIR}/akun_kandidat.csv"
    if not os.path.exists(path_a) or os.path.getsize(path_a) == 0:
        pd.DataFrame([{
            "username":      k["id"],
            "password_hash": hash_pw("kandidat123"),
            "kandidat_id":   k["id"],
        } for k in DUMMY_KANDIDAT]).to_csv(path_a, index=False)
 
    # 4. Skor penilaian K001-K008 (hanya tulis jika belum ada)
    for (dm_key, kid), skor_dict in DUMMY_SCORES.items():
        dm_info = KRITERIA_DM[dm_key]
        for subkrit, nilai in skor_dict.items():
            path_csv = f"{NILAI_DIR}/{dm_info['folder']}/{subkrit}.csv"
            if os.path.exists(path_csv) and os.path.getsize(path_csv) > 0:
                df = pd.read_csv(path_csv, index_col="id")
                df.index = df.index.astype(str)
            else:
                df = pd.DataFrame(columns=["nilai"])
                df.index.name = "id"
            if str(kid) not in df.index:
                df.loc[str(kid), "nilai"] = float(nilai)
                df.to_csv(path_csv)
 
