from config import AKUN_INTERNAL, ASESOR_BY_USERNAME, hash_pw
from database import load_akun_kandidat, load_pendaftar

# ═══════════════════════════════════════════════════════════════
# AUTENTIKASI
# ═══════════════════════════════════════════════════════════════

def get_kandidat_by_id(kid, records: list):
    return next((r for r in records if str(r.get("id")) == str(kid)), None)

def verify_login(username: str, password: str):
    """
    Urutan pengecekan:
    1. Akun internal (admin, DM, kepala)
    2. Akun asesor (dari ASESOR_POOL)
    3. Akun kandidat (dari CSV)
    Return: (role, user_dict) atau (None, None)
    """
    # 1. Akun internal
    akun = AKUN_INTERNAL.get(username)
    if akun and hash_pw(password) == hash_pw(akun["password_plain"]):
        return akun["role"], {
            "nama": akun["nama"], "username": username, **akun["info"]
        }

    # 2. Akun asesor
    asesor = ASESOR_BY_USERNAME.get(username)
    if asesor and hash_pw(password) == hash_pw(asesor["password_plain"]):
        return "asesor", {
            "nama":      asesor["nama"],
            "username":  username,
            "asesor_id": asesor["asesor_id"],
            "dm_key":    asesor["dm_key"],
            "bidang":    asesor["bidang"],
        }

    # 3. Akun kandidat
    df_akun = load_akun_kandidat()
    if not df_akun.empty:
        row = df_akun[df_akun["username"] == username]
        if not row.empty and hash_pw(password) == row.iloc[0]["password_hash"]:
            kid = str(row.iloc[0]["kandidat_id"])
            rec = get_kandidat_by_id(kid, load_pendaftar())
            return "kandidat", {
                "nama":     rec["nama"] if rec else username,
                "username": username,
                "kid":      kid,
            }

    return None, None
