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
                        cek_dokumen_administrasi,
                        match_asesor_kandidat, get_asesor_kandidat,
                        get_dm_asesor_overview, _bidang_cocok,
                        get_kandidat_by_id, generate_new_id,
                        status_badge, all_asesor_selesai)
from utils import render_sidebar, init_state
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════════════════════════
# HALAMAN: ADMIN
# ═══════════════════════════════════════════════════════════════

def page_admin():
    render_sidebar()
    st.title("Dashboard Admin")

    records = load_pendaftar()
    verif   = load_verifications()
    df_assign  = load_asesor_assignments()

    tab1, tab2, tab3 = st.tabs(["Verifikasi Kandidat", "Decision Maker", "Sistem & Laporan"])
    
    # ── Tab 1 ─────────────────────────────────────────────────
    with tab1:
        n_lolos      = sum(1 for v in verif.values() if v == "lolos")
        n_lolos_auto = sum(1 for v in verif.values() if v == "lolos_auto")
        n_tolak      = sum(1 for v in verif.values() if v == "tidak_lolos")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Kandidat",       len(records))
        c2.metric("Lolos Administrasi",   n_lolos)
        c3.metric("Menunggu Cek Dokumen", n_lolos_auto)
        c4.metric("Tidak Lolos",          n_tolak)
        st.markdown("---")

        with st.expander("Utilitas Demo — Auto-Verifikasi Massal"):
            st.caption("Loloskan semua kandidat yang menunggu verifikasi dokumen sekaligus.")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("Auto-Check Semua Pending",
                            use_container_width=True,
                            disabled=st.session_state.admin_closed):
                    from algorithms import auto_check_administrasi
                    changed = 0
                    for k in records:
                        kid_r = str(k.get("id", ""))
                        if verif.get(kid_r, "") == "pending":
                            flags = auto_check_administrasi(k)
                            verif[kid_r] = "tidak_lolos" if flags else "lolos_auto"
                            changed += 1
                    save_verifications(verif)
                    st.success(f"Auto-check selesai untuk {changed} kandidat!")
                    st.rerun()
            with col_b:
                if st.button("Auto-Verifikasi Semua",
                            use_container_width=True,
                            disabled=st.session_state.admin_closed):
                    for k in records:
                        kid_r = str(k.get("id", ""))
                        if verif.get(kid_r, "") == "lolos_auto":
                            verif[kid_r] = "lolos"
                    save_verifications(verif)
                    st.success("Auto-verifikasi selesai!")
                    st.rerun()
            with col_c:
                if st.button("Reset Semua ke Pending",
                            use_container_width=True,
                            disabled=st.session_state.admin_closed):
                    for k in records:
                        verif[str(k.get("id", ""))] = "pending"
                    save_verifications(verif)
                    st.info("Semua kandidat dikembalikan ke Pending.")
                    st.rerun()

        if not records:
            st.info("Belum ada kandidat yang mendaftar.")
        else:
            lolos_auto  = [k for k in records if verif.get(str(k.get("id")), "") == "lolos_auto"]
            sudah_lolos = [k for k in records if verif.get(str(k.get("id")), "") == "lolos"]
            tidak_lolos = [k for k in records if verif.get(str(k.get("id")), "") == "tidak_lolos"]

            # ── Menunggu verifikasi dokumen ────────────────────
            st.markdown("#### Menunggu Verifikasi Dokumen")
            st.caption("Kandidat berikut lolos auto-check. Periksa dokumen lalu putuskan lolos/tolak.")
            if not lolos_auto:
                st.info("Tidak ada kandidat yang menunggu verifikasi dokumen.")
            else:
                for k in lolos_auto:
                    kid       = str(k.get("id", ""))
                    flags_dok = cek_dokumen_administrasi(k)
                    with st.expander(
                        f"**{kid}** — {k.get('nama','—')}  |  "
                        f"{k.get('prodi','—')}, {k.get('universitas','—')}"
                    ):
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**IPK:** {float(k.get('ipk',0)):.2f}  \n"
                                    f"**Usia:** {k.get('usia','—')} thn")
                        c2.markdown(f"**UKBI:** {k.get('skor_ukbi','—')}  \n"
                                    f"**Bahasa:** {k.get('jenis_tes_bahasa','—')} "
                                    f"{k.get('skor_tes_bahasa','—')}")
                        c3.markdown(f"**LoA:** {'Ada' if k.get('file_loa_surat_aktif') else 'Tidak Ada' }  \n"
                                    f"**Rekomen:** {'Ada' if k.get('file_rekomendasi') else 'Tidak Ada'}")

                        st.markdown("### Dokumen Kandidat")
                        docs = {
                            "Surat Rekomendasi": k.get("file_rekomendasi"),
                            "LoA / Surat Aktif": k.get("file_loa_surat_aktif"),
                            "Rencana Studi":     k.get("file_rencana_studi"),
                            "Esai":              k.get("file_esai"),
                        }
                        for nama_dok, path in docs.items():
                            if isinstance(path, str) and os.path.exists(path):
                                with st.expander(f" {nama_dok}"):
                                    import base64
                                    with open(path, "rb") as pdf_file:
                                        pdf_data = pdf_file.read()
                                    base64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                                    st.markdown(
                                        f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
                                        f'width="100%" height="600" type="application/pdf"></iframe>',
                                        unsafe_allow_html=True
                                    )
                                    st.download_button(
                                        f"⬇️ Download {nama_dok}",
                                        data=pdf_data,
                                        file_name=os.path.basename(path),
                                        mime="application/pdf",
                                        key=f"dl_{kid}_{nama_dok}",
                                    )
                            else:
                                st.caption(f"_{nama_dok}: belum diupload_")

                        if flags_dok:
                            st.markdown("**Catatan Dokumen:**")
                            for ftype, fmsg in flags_dok:
                                (st.error if ftype == "error" else st.warning)(
                                    f"{'' if ftype=='error' else ''} {fmsg}"
                                )
                        else:
                            st.success("Semua dokumen tersedia")

                        if not st.session_state.admin_closed:
                            ca, cb = st.columns(2)
                            with ca:
                                if st.button("Loloskan", key=f"ok_{kid}",
                                             use_container_width=True):
                                    verif[kid] = "lolos"
                                    save_verifications(verif)
                                    st.rerun()
                            with cb:
                                if st.button("Tolak", key=f"no_{kid}",
                                             use_container_width=True):
                                    verif[kid] = "tidak_lolos"
                                    save_verifications(verif)
                                    st.rerun()
                        else:
                            st.info(f"Tahap ditutup. Status: **{status_badge(verif.get(kid,'—'))}**")

            # ── Lolos administrasi ─────────────────────────────
            st.markdown("---")
            st.markdown("#### Lolos Tahap Administrasi")
            if not sudah_lolos:
                st.info("Belum ada kandidat yang dinyatakan lolos administrasi.")
            else:
                rows_lolos = []
                for k in sudah_lolos:
                    kid = str(k.get("id", ""))
                    rows_lolos.append({
                        "ID":           kid,
                        "Nama":         k.get("nama", "—"),
                        "Prodi":        k.get("prodi", "—"),
                        "Universitas":  k.get("universitas", "—"),
                        "IPK":          f"{float(k.get('ipk',0)):.2f}",
                        "UKBI":         k.get("skor_ukbi", "—"),
                        "Bahasa":       f"{k.get('jenis_tes_bahasa','—')} {k.get('skor_tes_bahasa','—')}",
                    })
                st.dataframe(pd.DataFrame(rows_lolos), use_container_width=True, hide_index=True)

            # ── Tidak lolos ────────────────────────────────────
            st.markdown("---")
            st.markdown("#### Gugur Otomatis (Tidak Lolos Auto-Check)")
            st.caption("Kandidat berikut gugur karena tidak memenuhi syarat terukur.")
            if not tidak_lolos:
                st.info("Tidak ada kandidat yang gugur.")
            else:
                rows_tl = []
                for k in tidak_lolos:
                    kid   = str(k.get("id", ""))
                    # Hanya cek auto_check (numerik), tidak cek dokumen via os.path.exists
                    from algorithms import auto_check_administrasi
                    flags_auto = auto_check_administrasi(k)
                    masalah    = " | ".join(m for _, m in flags_auto) if flags_auto else "Ditolak Admin"
                    rows_tl.append({
                        "ID":      kid,
                        "Nama":    k.get("nama", "—"),
                        "Prodi":   k.get("prodi", "—"),
                        "Masalah": masalah,
                    })
                st.dataframe(pd.DataFrame(rows_tl), use_container_width=True, hide_index=True)

    # ── Tab 2 ─────────────────────────────────────────────────
    with tab2:

        st.subheader("Decision Maker (30 Asesor)")
        st.caption("Setiap asesor dicocokkan dengan kandidat berdasarkan kesamaan bidang.")

        nama_map  = {str(r["id"]): r.get("nama", "—") for r in records}

        for dm_key, dm_val in KRITERIA_DM.items():
            st.markdown(f"##### {dm_val['label']}")
            pool      = [a for a in ASESOR_POOL if a["dm_key"] == dm_key]
            rows_pool = []
            for a in pool:
                if not df_assign.empty:
                    # Ambil SEMUA kandidat yang diassign ke asesor ini
                    r_all = df_assign[df_assign["asesor_id"] == a["asesor_id"]]
                    if not r_all.empty:
                        for _, row in r_all.iterrows():
                            kid_assign = row["kandidat_id"]
                            rows_pool.append({
                                "Username":          a["username"],
                                "Nama Asesor":       a["nama"],
                                "Bidang":            a["bidang"],
                                "Kandidat Assigned": kid_assign,
                                "Nama Kandidat":     nama_map.get(str(kid_assign), "—"),
                            })
                    else:
                        rows_pool.append({
                            "Username":          a["username"],
                            "Nama Asesor":       a["nama"],
                            "Bidang":            a["bidang"],
                            "Kandidat Assigned": "Belum diassign",
                            "Nama Kandidat":     "—",
                        })
                else:
                    rows_pool.append({
                        "Username":          a["username"],
                        "Nama Asesor":       a["nama"],
                        "Bidang":            a["bidang"],
                        "Kandidat Assigned": "Belum diassign",
                        "Nama Kandidat":     "—",
                    })
            st.dataframe(pd.DataFrame(rows_pool),
                         use_container_width=True, hide_index=True)
            
    # ── Tab 3 ─────────────────────────────────────────────────
    with tab3:
        st.subheader("Penutupan Tahap Administrasi & Matching Asesor")
        n_pend_now  = sum(1 for v in verif.values() if v == "pending")
        n_lolos_now = sum(1 for v in verif.values() if v == "lolos")

        if not st.session_state.admin_closed:
            if n_pend_now > 0:
                st.warning(f"Masih ada **{n_pend_now} kandidat** yang belum diverifikasi.")
            else:
                st.success("Semua kandidat sudah diverifikasi.")

            if st.button(
                "Tutup Administrasi & Matching Asesor ↔ Kandidat",
                type="primary",
                disabled=(n_pend_now > 0),
                use_container_width=True,
            ):
                ids_lolos = [str(r["id"]) for r in records
                             if verif.get(str(r["id"])) == "lolos"]
                df_match  = match_asesor_kandidat(ids_lolos, records)
                save_asesor_assignments(df_match)
                save_admin_closed()                  # simpan ke file
                st.session_state.admin_closed = True
                st.success(
                    f"Tahap administrasi ditutup!\n\n"
                    f"**{n_lolos_now} kandidat lolos** dicocokkan dengan asesor.\n\n"
                    f"Total pasangan terbentuk: **{len(df_match)}**"
                )
                st.rerun()

            if n_pend_now > 0:
                st.caption("Tombol aktif setelah semua kandidat diverifikasi.")
        else:
            st.success(
                f"Tahap ditutup. **{n_lolos_now} kandidat lolos** "
                f"sudah dicocokkan dengan asesor."
            )
            st.metric("Total pasangan asesor ↔ kandidat", len(df_assign))

        st.markdown("---")
        st.subheader("Ekspor Laporan Administrasi")

        path_adm = f"{BASE_DIR}/laporan_administrasi.csv"

        if os.path.exists(path_adm):
            df_adm_saved = pd.read_csv(path_adm)
            st.info("Laporan administrasi sudah tersimpan.")
            st.dataframe(df_adm_saved, use_container_width=True, hide_index=True)
        else:
            if st.button("Simpan laporan_administrasi.csv", use_container_width=True):
                rows = []
                for k in records:
                    kid_r = str(k.get("id", ""))
                    flags = verifikasi_administrasi(k)
                    rows.append({
                        "ID":             kid_r,
                        "Nama":           k.get("nama", ""),
                        "Status":         verif.get(kid_r, "pending").upper(),
                        "Jumlah Masalah": len(flags),
                        "Masalah":        " | ".join(m for _, m in flags) if flags else "-",
                    })
                df_adm = pd.DataFrame(rows)
                df_adm.to_csv(path_adm, index=False)
                st.success(f"Tersimpan di {BASE_DIR}/laporan_administrasi.csv")
                st.dataframe(df_adm, use_container_width=True, hide_index=True)

                fig, axes = plt.subplots(1, 2, figsize=(12, 4))
                fig.suptitle("Verifikasi Administrasi", fontsize=13, fontweight="bold")
                jml_l = n_lolos_now
                jml_t = len(records) - jml_l
                axes[0].pie(
                    [jml_l, jml_t],
                    labels=[f"Lolos ({jml_l})", f"Tidak ({jml_t})"],
                    colors=["#2ecc71", "#e74c3c"], autopct="%1.0f%%", startangle=90
                )
                axes[0].set_title("Distribusi Hasil")
                kat = {"Rekomendasi":0,"Usia":0,"LoA/Aktif":0,"IPK":0,
                       "UKBI":0,"Bahasa Asing":0,"Rencana Studi":0,"Esai":0}
                kw  = {"rekomendasi":"Rekomendasi","usia":"Usia","loa":"LoA/Aktif",
                       "ipk":"IPK","ukbi":"UKBI","bahasa":"Bahasa Asing",
                       "rencana studi":"Rencana Studi","esai":"Esai"}
                for row in rows:
                    for fmsg in row["Masalah"].split(" | "):
                        for k_, v_ in kw.items():
                            if k_ in fmsg.lower():
                                kat[v_] += 1
                                break
                cats = list(kat.keys())
                vals = list(kat.values())
                bars = axes[1].barh(
                    cats, vals,
                    color=["#e74c3c" if v > 0 else "#bdc3c7" for v in vals]
                )
                axes[1].set_title("Jenis Masalah Administrasi")
                for bar, val in zip(bars, vals):
                    if val > 0:
                        axes[1].text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                                     str(val), va="center", fontweight="bold")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
                st.rerun()

