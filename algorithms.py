import numpy as np
import pandas as pd
from config import (KRITERIA_DM, ASESOR_POOL, ASESOR_BY_ID,
                    BATAS_BAHASA, BATAS_IPK, BATAS_UKBI,
                    BATAS_USIA_UMUM, BATAS_USIA_KULIAH)
from database import (load_asesor_assignments, load_pendaftar,
                      load_scores_kandidat)

# ═══════════════════════════════════════════════════════════════
# MATCHING ASESOR ↔ KANDIDAT
# ═══════════════════════════════════════════════════════════════

def _bidang_cocok(prodi: str, bidang: str) -> bool:
    """
    Cek kemiripan prodi kandidat dengan bidang asesor.
    Menggunakan pencocokan kata kunci dua arah (case-insensitive).
    """
    prodi  = prodi.lower().strip()
    bidang = bidang.lower().strip()
    if prodi == bidang:
        return True
    # Cek apakah salah satu kata dari bidang ada di prodi atau sebaliknya
    kata_bidang = set(bidang.split())
    kata_prodi  = set(prodi.split())
    return bool(kata_bidang & kata_prodi)

def match_asesor_kandidat(ids_lolos: list, records: list) -> pd.DataFrame:
    """
    Cocokkan setiap kandidat lolos dengan tepat 1 asesor per DM.

    Prioritas matching (3 putaran):
      1. Asesor yang bidangnya COCOK + beban paling sedikit
      2. Asesor yang bidangnya MIRIP (kata kunci sebagian) + beban paling sedikit
      3. Asesor mana saja dengan beban paling sedikit (round-robin)

    Tujuan: semua asesor mendapat minimal 1 kandidat jika memungkinkan,
    tidak ada asesor yang menumpuk terlalu banyak.
    """
    prodi_map = {str(r["id"]): r.get("prodi", "") for r in records}

    # Grup asesor per DM
    pool_per_dm = {dm_key: [a for a in ASESOR_POOL if a["dm_key"] == dm_key]
                   for dm_key in KRITERIA_DM}

    # Tracking beban: {dm_key: {asesor_id: jumlah_kandidat}}
    beban = {dm_key: {a["asesor_id"]: 0 for a in pool_per_dm[dm_key]}
             for dm_key in KRITERIA_DM}

    rows = []

    def _cocok_penuh(prodi, bidang):
        """Bidang persis sama atau semua kata cocok."""
        p, b = prodi.lower().strip(), bidang.lower().strip()
        return p == b or set(b.split()) == set(p.split())

    def _cocok_mirip(prodi, bidang):
        """Ada minimal 1 kata yang sama (lebih longgar)."""
        p, b = prodi.lower().strip(), bidang.lower().strip()
        return bool(set(b.split()) & set(p.split()))

    def _pilih_asesor(kandidat_asesor: list, beban_dm: dict):
        """Dari daftar kandidat asesor, pilih yang bebannya paling sedikit."""
        return min(kandidat_asesor, key=lambda a: beban_dm[a["asesor_id"]])

    for dm_key in KRITERIA_DM:
        pool_dm    = pool_per_dm[dm_key]
        beban_dm   = beban[dm_key]

        for kid in ids_lolos:
            prodi = prodi_map.get(str(kid), "")

            # Putaran 1: cocok penuh bidang, pilih yang beban paling sedikit
            kandidat_p1 = [a for a in pool_dm if _cocok_penuh(prodi, a["bidang"])]

            # Putaran 2: cocok mirip (kata kunci sebagian)
            kandidat_p2 = [a for a in pool_dm if _cocok_mirip(prodi, a["bidang"])
                           and a not in kandidat_p1]

            # Putaran 3: semua asesor (fallback)
            if kandidat_p1:
                terpilih = _pilih_asesor(kandidat_p1, beban_dm)
            elif kandidat_p2:
                terpilih = _pilih_asesor(kandidat_p2, beban_dm)
            else:
                terpilih = _pilih_asesor(pool_dm, beban_dm)

            beban_dm[terpilih["asesor_id"]] += 1
            rows.append({
                "asesor_id":   terpilih["asesor_id"],
                "kandidat_id": str(kid),
                "dm_key":      dm_key,
                "status":      "assigned",
            })

    return pd.DataFrame(rows)

def get_asesor_kandidat(asesor_id: str) -> list:
    """Dapatkan list kandidat_id yang diassign ke asesor tertentu."""
    df = load_asesor_assignments()
    if df.empty:
        return []
    return list(df[df["asesor_id"] == asesor_id]["kandidat_id"].astype(str))

def get_dm_asesor_overview(dm_key: str) -> pd.DataFrame:
    """
    Ringkasan progress penilaian semua asesor di bawah satu DM.
    Setiap baris = 1 asesor × 1 kandidat (asesor bisa muncul >1 baris).
    """
    df_assign = load_asesor_assignments()
    if df_assign.empty:
        return pd.DataFrame()
 
    dm_assign = df_assign[df_assign["dm_key"] == dm_key]
    sks       = [k["nama"] for k in KRITERIA_DM[dm_key]["kriteria"]]
    records   = load_pendaftar()
    nama_map  = {str(r["id"]): r.get("nama",  "—") for r in records}
    prodi_map = {str(r["id"]): r.get("prodi", "—") for r in records}
 
    rows = []
    for _, row in dm_assign.iterrows():
        asesor  = ASESOR_BY_ID.get(row["asesor_id"], {})
        kid     = str(row["kandidat_id"])
        nilai   = load_scores_kandidat(dm_key, kid)
        selesai = all(sk in nilai for sk in sks)
 
        rows.append({
            "Asesor ID":     row["asesor_id"],
            "Nama Asesor":   asesor.get("nama",   "—"),
            "Bidang":        asesor.get("bidang",  "—"),
            "Kandidat ID":   kid,
            "Nama Kandidat": nama_map.get(kid,  "—"),
            "Prodi":         prodi_map.get(kid, "—"),
            "Status Nilai":  "Selesai" if selesai else "Belum",
        })
 
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════
# HELPER UMUM
# ═══════════════════════════════════════════════════════════════

def get_kandidat_by_id(kid, records: list):
    return next((r for r in records if str(r.get("id")) == str(kid)), None)

def generate_new_id(records: list) -> str:
    if not records:
        return "K001"
    nums = []
    for r in records:
        try:
            nums.append(int(str(r["id"]).replace("K", "")))
        except Exception:
            pass
    return f"K{(max(nums) + 1):03d}" if nums else "K001"

def status_badge(status: str) -> str:
    icons  = {"lolos":"🟢","tidak_lolos":"🔴","pending":"🟡"}
    labels = {"lolos":"Lolos","tidak_lolos":"Tidak Lolos","pending":"Pending"}
    return f"{icons.get(status,'⚪')} {labels.get(status,'—')}"

def all_asesor_selesai(ids_lolos: list) -> bool:
    """Cek apakah semua asesor sudah menyelesaikan penilaian."""
    df_assign = load_asesor_assignments()
    if df_assign.empty:
        return False
    for dm_key, dm_info in KRITERIA_DM.items():
        sks = [k["nama"] for k in dm_info["kriteria"]]
        for kid in ids_lolos:
            nilai = load_scores_kandidat(dm_key, str(kid))
            if not all(sk in nilai for sk in sks):
                return False
    return True

# ═══════════════════════════════════════════════════════════════
# ALGORITMA TOPSIS
# ═══════════════════════════════════════════════════════════════

def topsis(matriks: pd.DataFrame, kriteria_list: list) -> pd.Series:
    X    = matriks.values.astype(float)
    n, m = X.shape

    norm       = np.sqrt((X ** 2).sum(axis=0))
    norm[norm == 0] = 1e-10
    R = X / norm

    bobot = np.array([k["bobot"] for k in kriteria_list])
    V     = R * bobot

    A_plus  = np.array([V[:,j].max() if kriteria_list[j]["tipe"]=="benefit"
                        else V[:,j].min() for j in range(m)])
    A_minus = np.array([V[:,j].min() if kriteria_list[j]["tipe"]=="benefit"
                        else V[:,j].max() for j in range(m)])

    D_plus  = np.sqrt(((V - A_plus)  ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))

    denom       = D_plus + D_minus
    denom[denom == 0] = 1e-10
    Ci = D_minus / denom

    return pd.Series(Ci, index=matriks.index, name="Skor_TOPSIS")

# ═══════════════════════════════════════════════════════════════
# ALGORITMA BORDA COUNT  (dari Kode 2)
# ═══════════════════════════════════════════════════════════════

def borda_count(ranking_dict: dict, kandidat_ids: list) -> pd.Series:
    n      = len(kandidat_ids)
    scores = pd.Series(0.0, index=[str(i) for i in kandidat_ids])
    for _, ranking in ranking_dict.items():
        for kid in kandidat_ids:
            kid_str = str(kid)
            if kid_str in ranking.index:
                scores[kid_str] += (n - int(ranking[kid_str]))
    return scores

# ═══════════════════════════════════════════════════════════════
# VERIFIKASI ADMINISTRASI
# ═══════════════════════════════════════════════════════════════

def cek_bahasa(jenis: str, skor: float):
    if jenis not in BATAS_BAHASA:
        return False, f"Jenis tes tidak dikenal: {jenis}"
    minimal = BATAS_BAHASA[jenis]
    lolos   = float(skor) >= minimal
    return lolos, (f"{jenis} {skor} ≥ {minimal} " if lolos
                   else f"{jenis} {skor} < {minimal} (min {minimal})")

def auto_check_administrasi(k: dict) -> list:
    flags = []

    usia     = int(k.get("usia", 99))
    s_kuliah = str(k.get("sedang_kuliah", "False")).lower() in ("true", "1", "yes")
    batas    = BATAS_USIA_KULIAH if s_kuliah else BATAS_USIA_UMUM
    if usia > batas:
        flags.append(("error", f"Usia {usia} thn melebihi batas {batas} thn"))

    if float(k.get("ipk", 0)) < BATAS_IPK:
        flags.append(("error", f"IPK {float(k.get('ipk',0)):.2f} < minimal {BATAS_IPK}"))

    if int(float(k.get("skor_ukbi", 0))) < BATAS_UKBI:
        flags.append(("error", f"UKBI {k.get('skor_ukbi','?')} < minimal {BATAS_UKBI}"))

    jenis = str(k.get("jenis_tes_bahasa", ""))
    skor  = float(k.get("skor_tes_bahasa", 0))
    ok, pesan = cek_bahasa(jenis, skor)
    if not ok:
        flags.append(("error", f"Bahasa asing: {pesan}"))

    return flags

def cek_dokumen_administrasi(k: dict) -> list:
    import os
    flags = []

    def _ada(val):
        return bool(str(val or "").strip()) and os.path.exists(str(val).strip())

    if not _ada(k.get("file_rekomendasi")):
        flags.append(("error", "Surat rekomendasi tidak ada"))

    if not _ada(k.get("file_loa_surat_aktif")):
        flags.append(("warning", "Surat LoA/Surat Aktif tidak ada"))

    if not _ada(k.get("file_rencana_studi")):
        flags.append(("error", "File rencana studi tidak ada"))

    if not _ada(k.get("file_esai")):
        flags.append(("error", "File esai tidak ada"))

    return flags

def verifikasi_administrasi(k: dict) -> list:
    return auto_check_administrasi(k) + cek_dokumen_administrasi(k)
