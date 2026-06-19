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
from auth import verify_login
from algorithms import (topsis, borda_count, verifikasi_administrasi,
                        match_asesor_kandidat, get_asesor_kandidat,
                        get_dm_asesor_overview, _bidang_cocok,
                        get_kandidat_by_id, generate_new_id,
                        status_badge, all_asesor_selesai)
from utils import render_sidebar, init_state

# ═══════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════

def _safe_int(val, default):
    try:
        result = int(float(val))
        return result
    except (TypeError, ValueError):
        return default

def _safe_float(val, default):
    try:
        result = float(val)
        if result != result:  # cek NaN
            return default
        return result
    except (TypeError, ValueError):
        return default

# ═══════════════════════════════════════════════════════════════
# HALAMAN: KANDIDAT
# ═══════════════════════════════════════════════════════════════

def page_kandidat():
    render_sidebar()
    kid     = st.session_state.user.get("kid")
    records = load_pendaftar()
    k       = get_kandidat_by_id(kid, records)
    verif   = load_verifications()
    status  = verif.get(str(kid), "pending")

    if not k:
        st.error("Data kandidat tidak ditemukan. Hubungi Admin.")
        return

    st.title("Dashboard Kandidat")
    st.markdown(f"Selamat datang, **{k['nama']}** `({kid})`")
    st.caption(f"Mendaftar: {k.get('tanggal_daftar','—')}")
    st.markdown("---")

    # sudah_daftar: mengontrol akses tab (form pernah diisi atau belum)
    sudah_daftar = (
        str(k.get("pendaftaran_lengkap", "False")).lower() in ("true", "1")
        or bool(str(k.get("universitas", "")).strip())
    )

    # form_terkirim: khusus label status tahap Pendaftaran
    form_terkirim = str(k.get("pendaftaran_lengkap", "False")).lower() in ("true", "1")

    tab_status, tab_daftar = st.tabs(["Status Aplikasi", "Formulir Pendaftaran Beasiswa"])

    # ── Tab Status ────────────────────────────────────────────
    with tab_status:
        if not form_terkirim:
            st.warning("Anda belum mengirim formulir pendaftaran beasiswa. Silakan lengkapi di tab 'Formulir Pendaftaran Beasiswa'.")

        if sudah_daftar:
            cols = st.columns(5)
            labels = ["Universitas", "Program Studi", "IPK", "UKBI", "Usia"]
            values = [
                k.get("universitas","—"),
                k.get("prodi","—"),
                f"{_safe_float(k.get('ipk'), 0.0):.2f}",
                str(k.get("skor_ukbi","—")),
                f"{k.get('usia','—')} thn",
            ]
            for col, lbl, val in zip(cols, labels, values):
                with col:
                    st.markdown(f"<p style='font-size:11px;color:gray;margin-bottom:2px'>{lbl}</p>"
                                f"<p style='font-size:13px;font-weight:500;margin:0'>{val}</p>",
                                unsafe_allow_html=True)

            st.markdown("---")

        st.subheader("Status Aplikasi")

        gagal_admin = (status == "tidak_lolos")

        gagal_substansi = False
        override        = False
        ditetapkan      = False

        if st.session_state.borda_done and status == "lolos":
            path_final = f"{BASE_DIR}/laporan_penetapan_final.csv"
            if os.path.exists(path_final):
                df_f = pd.read_csv(path_final)
                if "ID" in df_f.columns:
                    df_f["ID"] = df_f["ID"].astype(str)
                    row_f = df_f[df_f["ID"] == str(kid)]
                    if not row_f.empty:
                        stat_p = str(row_f.iloc[0].get("Status Penetapan", ""))
                        if stat_p.startswith("DITETAPKAN"):
                            ditetapkan = True
                        elif "OVERRIDE" in stat_p.upper():
                            override = True
                        else:
                            gagal_substansi = True
                    else:
                        # Lolos admin tapi tidak ada di laporan final = tidak masuk kuota
                        gagal_substansi = True

        verif_sudah_berjalan     = status in ("lolos", "tidak_lolos")
        substansi_sudah_berjalan = st.session_state.borda_done and status == "lolos"

        tahap = [
            (
                "Pendaftaran",
                "Selesai" if form_terkirim else "Belum Dilengkapi",
                "ok" if form_terkirim else "tunggu",
            ),
            (
                "Verifikasi Administrasi",
                "Lolos"          if status == "lolos"       else
                "Tidak Lolos"    if status == "tidak_lolos" else
                "Belum Diproses" if not form_terkirim       else
                "Sedang Diproses",
                "ok"    if status == "lolos"       else
                "gagal" if status == "tidak_lolos" else
                "tunggu",
            ),
            (
                "Penilaian Substansi",
                "Belum Dimulai" if not verif_sudah_berjalan  else
                "Gugur"         if gagal_admin                else
                "Selesai"       if substansi_sudah_berjalan   else
                "Menunggu Hasil",
                "tunggu" if not verif_sudah_berjalan  else
                "gagal"  if gagal_admin                else
                "ok"     if substansi_sudah_berjalan   else
                "tunggu",
            ),
            (
                "Hasil Final",
                "Belum Dimulai" if not verif_sudah_berjalan        else
                "Gugur"         if gagal_admin                      else
                "Tidak Lolos"   if (gagal_substansi or override)   else
                "Lolos"         if ditetapkan                       else
                "Menunggu Hasil",
                "tunggu" if not verif_sudah_berjalan        else
                "gagal"  if gagal_admin                     else
                "gagal"  if (gagal_substansi or override)  else
                "ok"     if ditetapkan                      else
                "tunggu",
            ),
        ]

        for label, val, state in tahap:
            ca, cb = st.columns([6, 1])
            with ca:
                st.markdown(f"**{label}**")
                st.caption(val)
            st.markdown("---")

        # ── Pesan hasil akhir ───────────────────────────────────
        if status == "tidak_lolos":
            st.error(
                "Anda dinyatakan **tidak lolos tahap administrasi** "
                "dan tidak dapat melanjutkan ke tahap selanjutnya."
            )
        elif status == "lolos" and not st.session_state.borda_done:
            st.success(
                "Selamat Anda lolos tahap administrasi. "
                "Silahkan tunggu informasi untuk tahap selanjutnya."
            )
        elif st.session_state.penetapan_done and status == "lolos":
            if ditetapkan:
                st.success(
                    "Selamat Anda dinyatakan **lolos seleksi Beasiswa Unggulan**. "
                    "Silakan tunggu informasi selanjutnya melalui website Beasiswa Unggulan."
                )
            else:
                st.error(
                    "Anda dinyatakan **tidak lolos Beasiswa Unggulan**."
                )

    # ── Tab Formulir Pendaftaran ──────────────────────────────
    with tab_daftar:
        if form_terkirim and status != "pending":
            st.info("Formulir pendaftaran sudah disubmit dan sedang diproses. Data tidak dapat diubah.")
            return

        _form_pendaftaran_beasiswa(kid, k, records)


def _form_pendaftaran_beasiswa(kid, k, records):
    st.subheader("Formulir Pendaftaran Beasiswa")

    with st.form("form_beasiswa", clear_on_submit=False):
        st.markdown("##### Data Pribadi")
        c1, c2 = st.columns(2)
        with c1:
            usia = st.number_input("Usia (tahun)", 18, 60,
                                   _safe_int(k.get("usia"), 24))
        with c2:
            sedang_kuliah = st.checkbox(
                "Sedang Aktif Kuliah",
                value=str(k.get("sedang_kuliah", "False")).lower() in ("true", "1"),
                help="Batas usia menjadi 33 tahun jika dicentang"
            )

        st.markdown("##### Data Akademik")
        c1, c2, c3 = st.columns(3)
        with c1:
            universitas = st.text_input("Universitas Tujuan",
                                        value=k.get("universitas", "") or "")
        with c2:
            prodi = st.text_input("Program Studi",
                                  value=k.get("prodi", "") or "",
                                  help="Contoh: Ilmu Komputer, Manajemen, Kedokteran")
        with c3:
            ipk = st.number_input("IPK (skala 4.00)", 0.0, 4.0,
                                   _safe_float(k.get("ipk"), 3.50), 0.01, format="%.2f")

        st.markdown("##### Skor Bahasa Inggris")
        c1, c2 = st.columns(2)
        with c1:
            jenis_tes = st.selectbox("Jenis Tes",
                                     ["ITP", "PTE", "IBT", "IELTS"],
                                     index=["ITP","PTE","IBT","IELTS"].index(
                                         k.get("jenis_tes_bahasa","ITP")
                                         if k.get("jenis_tes_bahasa") in ["ITP","PTE","IBT","IELTS"]
                                         else "ITP"
                                     ))
        with c2:
            skor_tes = st.number_input("Skor Tes", 0.0, 990.0,
                                        _safe_float(k.get("skor_tes_bahasa"), 550.0),
                                        0.5, format="%.1f")

        st.markdown("##### Skor UKBI")
        skor_ukbi = st.number_input("Skor UKBI", 0, 800,
                                     _safe_int(k.get("skor_ukbi"), 578))

        st.markdown("##### Dokumen")
        st.caption("Setiap kolom hanya menerima 1 file PDF.")
        c1, c2 = st.columns(2)
        with c1:
            file_rek  = st.file_uploader(
                "Upload Surat Rekomendasi", type=["pdf"],
                accept_multiple_files=False, key="up_rek"
            )
            file_loa  = st.file_uploader(
                "Upload LoA / Surat Aktif", type=["pdf"],
                accept_multiple_files=False, key="up_loa"
            )
            file_rs   = st.file_uploader(
                "Upload Rencana Studi", type=["pdf"],
                accept_multiple_files=False, key="up_rs"
            )
        with c2:
            file_esai = st.file_uploader(
                "Upload Esai", type=["pdf"],
                accept_multiple_files=False, key="up_esai"
            )

        setuju    = st.checkbox("Saya menyatakan data yang saya isi adalah benar.")
        submitted = st.form_submit_button("Kirim Pendaftaran",
                                          use_container_width=True, type="primary")

    if submitted:
        errs = []

        def _file_valid(upload, existing_path):
            if upload is not None:
                return True
            return bool(str(existing_path or "").strip()) and os.path.exists(str(existing_path).strip())

        if not universitas.strip():
            errs.append("Universitas wajib diisi.")
        if not prodi.strip():
            errs.append("Program studi wajib diisi.")
        if ipk == 0.0:
            errs.append("IPK wajib diisi (tidak boleh 0).")
        if skor_ukbi == 0:
            errs.append("Skor UKBI wajib diisi (tidak boleh 0).")
        if skor_tes == 0.0:
            errs.append("Skor tes bahasa wajib diisi (tidak boleh 0).")
        if not _file_valid(file_rek, k.get("file_rekomendasi")):
            errs.append("Surat Rekomendasi wajib diupload.")
        if not _file_valid(file_loa, k.get("file_loa_surat_aktif")):
            errs.append("File LoA / Surat Aktif wajib diupload.")
        if not _file_valid(file_rs, k.get("file_rencana_studi")):
            errs.append("File Rencana Studi wajib diupload.")
        if not _file_valid(file_esai, k.get("file_esai")):
            errs.append("File Esai wajib diupload.")
        if not setuju:
            errs.append("Setujui pernyataan konfirmasi.")

        if errs:
            for e in errs:
                st.error(e)
            return

        def save_uploaded_file(uploaded_file, folder, existing_val="", label=""):
            if uploaded_file is None:
                return existing_val
            os.makedirs(folder, exist_ok=True)
            ext      = os.path.splitext(uploaded_file.name)[1] or ".pdf"
            filename = f"{label}_{kid}{ext}"
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return filepath

        path_rek  = save_uploaded_file(file_rek,  os.path.join("uploads", "rekomendasi"),  k.get("file_rekomendasi", ""),     "rekomendasi")
        path_loa  = save_uploaded_file(file_loa,  os.path.join("uploads", "loa"),           k.get("file_loa_surat_aktif", ""), "loa")
        path_rs   = save_uploaded_file(file_rs,   os.path.join("uploads", "rencana_studi"), k.get("file_rencana_studi", ""),   "rencana_studi")
        path_esai = save_uploaded_file(file_esai, os.path.join("uploads", "esai"),          k.get("file_esai", ""),            "esai")

        updated_records = []
        for r in records:
            if str(r.get("id")) == str(kid):
                r.update({
                    "usia":               usia,
                    "sedang_kuliah":      sedang_kuliah,
                    "universitas":        universitas.strip(),
                    "prodi":              prodi.strip(),
                    "ipk":                ipk,
                    "jenis_tes_bahasa":   jenis_tes,
                    "skor_tes_bahasa":    skor_tes,
                    "skor_ukbi":          skor_ukbi,
                    "file_rekomendasi":   path_rek,
                    "file_loa_surat_aktif": path_loa,
                    "file_rencana_studi": path_rs,
                    "file_esai":          path_esai,
                    "pendaftaran_lengkap": True,
                })
            updated_records.append(r)
        save_pendaftar(updated_records)

        from algorithms import verifikasi_administrasi
        flags = verifikasi_administrasi({
            "usia":              usia,
            "sedang_kuliah":     sedang_kuliah,
            "ipk":               ipk,
            "skor_ukbi":         skor_ukbi,
            "jenis_tes_bahasa":  jenis_tes,
            "skor_tes_bahasa":   skor_tes,
            "file_rekomendasi":  path_rek,
            "file_loa_surat_aktif": path_loa,
            "file_rencana_studi": path_rs,
            "file_esai":         path_esai,
        })

        verif = load_verifications()
        if any(f[0] == "error" for f in flags):
            verif[str(kid)] = "tidak_lolos"
            save_verifications(verif)
            st.error("Pendaftaran diterima, namun Anda tidak memenuhi syarat administrasi berikut:")
            for ftype, fmsg in flags:
                if ftype == "error":
                    st.error(f"{fmsg}")
        else:
            verif[str(kid)] = "lolos_auto"
            save_verifications(verif)
            st.success("Pendaftaran berhasil! Data Anda memenuhi syarat administrasi dan akan diverifikasi dokumen oleh Admin.")

        st.rerun()