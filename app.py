"""
GDSS Beasiswa Unggulan S2
=========================
Entry point aplikasi. Jalankan dengan:
    streamlit run app.py

Struktur file:
    app.py          → Entry point + konfigurasi halaman + main()
    config.py       → Konstanta, asesor pool, data dummy
    database.py     → Fungsi baca/tulis file CSV
    auth.py         → Autentikasi login
    algorithms.py   → TOPSIS, Borda, verifikasi, matching asesor
    utils.py        → Session state, sidebar
    pages/
        login.py    → Halaman login + form pendaftaran
        kandidat.py → Dashboard kandidat
        admin.py    → Dashboard admin
        asesor.py   → Dashboard asesor (input nilai)
        kepala.py   → Dashboard kepala puslapdik
"""

import streamlit as st

# ── Konfigurasi halaman (HARUS dipanggil pertama kali) ──
st.set_page_config(
    page_title="GDSS Beasiswa Unggulan S2",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    [data-testid="InputInstructions"] { display: none; }
    </style>
""", unsafe_allow_html=True)

from config import init_dirs
from utils import init_state
from pages.login import page_login
from pages.kandidat import page_kandidat
from pages.admin import page_admin
from pages.asesor import page_asesor
from pages.kepala import page_kepala

init_dirs()

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
    elif role == "asesor":
        page_asesor()
    elif role == "kepala":
        page_kepala()

if __name__ == "__main__":
    main()