import streamlit as st
import pandas as pd
import os
from config import (BASE_DIR, NILAI_DIR, KRITERIA_DM, KUOTA_BEASISWA,
                    ASESOR_POOL, ASESOR_BY_ID, AKUN_INTERNAL)
from database import (load_pendaftar, save_pendaftar,
                      load_verifications, save_verifications,
                      load_akun_kandidat, save_akun_kandidat,
                      load_asesor_assignments, save_asesor_assignments,
                      load_scores_kandidat, load_scores_all_dm,
                      save_score, load_admin_closed, save_admin_closed)
# from auth import verify_login
from auth import verify_login, hash_pw
from algorithms import (topsis, borda_count, verifikasi_administrasi,
                        match_asesor_kandidat, get_asesor_kandidat,
                        get_dm_asesor_overview, _bidang_cocok,
                        get_kandidat_by_id, generate_new_id,
                        status_badge, all_asesor_selesai)
from utils import render_sidebar, init_state
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# HALAMAN: LOGIN
# ═══════════════════════════════════════════════════════════════

def page_login():
    st.markdown(
        "<h1 style='text-align:center;padding-top:2rem'>"
        "GDSS Seleksi Beasiswa Unggulan S2</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:gray'>"
        "Group Decision Support System — Puslapdik Kemdikbud</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        tab_login, tab_daftar = st.tabs(["Login", "Daftar Akun Baru"])

        # ── Tab Login ─────────────────────────────────────────
        with tab_login:
            st.subheader("Masuk ke Sistem")
            username = st.text_input("Username", placeholder="contoh: admin, asesor_dm1_01, K001")
            password = st.text_input("Password", type="password")

            if st.button("Masuk", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Username dan password wajib diisi.")
                else:
                    role, user_dict = verify_login(username.strip(), password)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.role      = role
                        st.session_state.user      = user_dict
                        st.rerun()
                    else:
                        st.error("Username atau password salah.")

            st.markdown("---")
            with st.expander("Akun Demo"):
                st.markdown("""
**Admin & DM & Kepala:**
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `kepala` | `kepala123` | Kepala Puslapdik |

**Asesor** (30 akun): password semua `asesor123`
- `asesor_dm1_01` s/d `asesor_dm1_10` → DM Esai
- `asesor_dm2_01` s/d `asesor_dm2_10` → DM Rencana Studi
- `asesor_dm3_01` s/d `asesor_dm3_10` → DM Wawancara

**Kandidat**: login dengan ID (mis. `K001`), password `kandidat123`
                """)

        # ── Tab Daftar ────────────────────────────────────────
        with tab_daftar:
            _form_buat_akun()

def _form_buat_akun():
    st.subheader("Buat Akun Kandidat")

    with st.form("form_buat_akun", clear_on_submit=True):
        nama     = st.text_input("Nama Lengkap")
        username = st.text_input("Username", placeholder="contoh: john.doe")
        password = st.text_input("Password", type="password")
        konfirm  = st.text_input("Konfirmasi Password", type="password")
        submitted = st.form_submit_button("Buat Akun", use_container_width=True, type="primary")

    if submitted:
        errs = []
        if not nama.strip():     errs.append("Nama lengkap wajib diisi.")
        if not username.strip(): errs.append("Username wajib diisi.")
        if not password:         errs.append("Password wajib diisi.")
        if password != konfirm:  errs.append("Password dan konfirmasi tidak cocok.")

        # Cek username sudah ada
        df_akun = load_akun_kandidat()
        if not df_akun.empty and username.strip() in df_akun["username"].values:
            errs.append("Username sudah digunakan.")

        if errs:
            for e in errs:
                st.error(f"{e}")
            return

        records = load_pendaftar()
        new_id  = generate_new_id(records)

        new_rec = {
            "id": new_id, "nama": nama.strip(),
            "usia": "", "sedang_kuliah": False,
            "universitas": "", "prodi": "", "ipk": "",
            "jenis_tes_bahasa": "", "skor_tes_bahasa": "",
            "skor_ukbi": "",
            "file_rekomendasi": "", "file_loa_surat_aktif": "",
            "file_rencana_studi": "", "file_esai": "",
            "esai_kata": "", "tanggal_daftar": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pendaftaran_lengkap": False,
        }
        records.append(new_rec)
        save_pendaftar(records)

        verif = load_verifications()
        verif[new_id] = "pending"
        save_verifications(verif)

        df_akun = load_akun_kandidat()
        df_akun = pd.concat([df_akun, pd.DataFrame([{
            "username": username.strip(),
            "password_hash": hash_pw(password),
            "kandidat_id": new_id,
        }])], ignore_index=True)
        save_akun_kandidat(df_akun)

        st.success(f"""
Akun berhasil dibuat!

- ID Kandidat: `{new_id}`
- Username: `{username.strip()}`

Silakan login dan lengkapi formulir pendaftaran beasiswa di dashboard Anda.
        """)

