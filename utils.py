import os
import streamlit as st
from config import KRITERIA_DM, BASE_DIR
from database import (load_admin_closed, load_substansi_closed,
                      load_penetapan_final, seed_dummy_data)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

def init_state():
    if "ready" not in st.session_state:
        st.session_state.ready        = True
        st.session_state.logged_in    = False
        st.session_state.role         = None
        st.session_state.user         = None
        st.session_state.borda_done   = False
        st.session_state.topsis_cache = {}
        seed_dummy_data()

    # Sinkronkan semua penanda tahap dari file
    st.session_state.admin_closed     = load_admin_closed()
    st.session_state.substansi_closed = load_substansi_closed()
    st.session_state.penetapan_done   = load_penetapan_final()

    # borda_done ikut substansi_closed agar persisten
    if st.session_state.substansi_closed:
        st.session_state.borda_done = True

    # Rebuild topsis_cache dari file jika kosong tapi substansi sudah selesai
    if st.session_state.borda_done and not st.session_state.topsis_cache:
        _rebuild_topsis_cache()


def _rebuild_topsis_cache():
    """Rebuild topsis_cache dari laporan_hasil_seleksi.csv saat login ulang."""
    import pandas as pd
    path_seleksi = f"{BASE_DIR}/laporan_hasil_seleksi.csv"
    if not os.path.exists(path_seleksi):
        return
    try:
        df = pd.read_csv(path_seleksi)
        df["ID"] = df["ID"].astype(str)
        if "Ranking Final" not in df.columns or "Total Poin" not in df.columns:
            return
        ranking_final = pd.Series(
            df["Ranking Final"].values,
            index=df["ID"].values,
        )
        borda_scores = pd.Series(
            df["Total Poin"].values,
            index=df["ID"].values,
            dtype=float,
        )
        nama_col = df["Nama"] if "Nama" in df.columns else df["ID"]
        st.session_state.topsis_cache = {
            "skor":          {},
            "ranking":       {},
            "borda":         borda_scores,
            "ranking_final": ranking_final,
            "ids_lolos":     list(df["ID"].values),
            "nama_map":      dict(zip(df["ID"].astype(str), nama_col)),
        }
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("## GDSS Beasiswa Unggulan S2")
        st.markdown("---")
        role_label = {
            "kandidat": "Kandidat",
            "admin":    "Admin",
            "asesor":   "Asesor",
            "dm":       "Decision Maker",
            "kepala":   "Kepala Puslapdik",
        }
        st.markdown(f"**{st.session_state.user.get('nama','—')}**")
        st.caption(role_label.get(st.session_state.role, ""))

        if st.session_state.role == "asesor":
            st.caption(f"Bidang: {st.session_state.user.get('bidang','—')}")
            st.caption(f"DM: {KRITERIA_DM.get(st.session_state.user.get('dm_key',''), {}).get('label','—')}")

        st.markdown("---")

        if st.button("Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role      = None
            st.session_state.user      = None
            st.rerun()