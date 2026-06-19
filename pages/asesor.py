import streamlit as st
import pandas as pd
import os
import base64
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
import random

# ═══════════════════════════════════════════════════════════════
# HALAMAN: ASESOR
# ═══════════════════════════════════════════════════════════════

def _default_nilai(kid: str, subkrit: str) -> int:
    """
    Generate nilai default dummy per kandidat per subkriteria.
    Deterministik (selalu sama), range 55–90, di atas 50.
    """
    seed = sum(ord(c) for c in str(kid) + subkrit)
    import random
    rng = random.Random(seed)
    return rng.randint(55, 90)

# ═══════════════════════════════════════════════════════════════
# HALAMAN: ASESOR  (BARU — role utama untuk input nilai)
# ═══════════════════════════════════════════════════════════════

def page_asesor():
    render_sidebar()
    asesor_id = st.session_state.user.get("asesor_id")
    dm_key    = st.session_state.user.get("dm_key")
    bidang    = st.session_state.user.get("bidang","—")
    dm_info   = KRITERIA_DM.get(dm_key, {})

    st.title("Dashboard Asesor")
    st.markdown(
        f"**{st.session_state.user['nama']}**  |  "
        f"Bidang: **{bidang}**  |  "
        f"Kriteria: **{dm_info.get('label','—')}**"
    )

    if not st.session_state.admin_closed:
        st.warning("Tahap administrasi belum ditutup. Kandidat belum diassign.")
        return

    if st.session_state.get("substansi_closed", False):
        st.success(
            "Proses penilaian substansi telah selesai."
        )
        return

    # Kandidat yang diassign ke asesor ini
    kids_assigned = get_asesor_kandidat(asesor_id)
    if not kids_assigned:
        st.info(
            "Anda belum mendapatkan kandidat yang diassign.\n\n"
            "Kemungkinan tidak ada kandidat dengan bidang yang cocok dengan Anda, "
            "atau matching belum dilakukan oleh Admin."
        )
        return

    records  = load_pendaftar()
    sks      = [k["nama"] for k in dm_info.get("kriteria", [])]
    kriteria_list = dm_info.get("kriteria", [])

    # Hitung progress
    done  = sum(1 for kid in kids_assigned
                if all(sk in load_scores_kandidat(dm_key, kid) for sk in sks))
    total = len(kids_assigned)
    st.progress(done/total if total else 0,
                text=f"Progress: {done}/{total} kandidat selesai dinilai")
    st.markdown("---")

    with st.expander("Panduan Penilaian"):
        st.markdown(f"**Kriteria yang Anda nilai:** {dm_info.get('label','—')}")
        st.markdown("**Subkriteria & Bobot:**")
        for k in kriteria_list:
            st.markdown(f"- **{k['nama'].replace('_',' ')}**: {k['bobot']*100:.0f}%")
        st.caption("Berikan nilai 0–100 untuk setiap subkriteria kandidat yang diassign kepada Anda.")
        st.caption(
            "Pencocokan berdasarkan kesamaan bidang pendidikan Anda dengan "
            "program studi kandidat."
        )

    st.subheader("Input Penilaian Kandidat")

    for kid in kids_assigned:
        k       = get_kandidat_by_id(kid, records)
        # st.write(k)
        nama_k  = k["nama"] if k else kid
        prodi_k = k.get("prodi","—") if k else "—"
        ex      = load_scores_kandidat(dm_key, str(kid))
        is_done = all(sk in ex for sk in sks)

        with st.expander(
            f"{'' if is_done else ''} **{kid}** — {nama_k}  |  "
            f"{prodi_k}  |  {'Selesai' if is_done else 'Belum dinilai'}"
        ):
            if k:
                st.caption(
                    f"Universitas: {k.get('universitas','—')}  |  "
                    f"IPK: {float(k.get('ipk',0)):.2f}  |  "
                    f"Usia: {k.get('usia','—')} thn"
                )
            # ==================================================
            # TAMPILKAN DOKUMEN YANG AKAN DINILAI
            # ==================================================

            if dm_key == "DM1_Esai":
                pdf_path = k.get("file_esai")
                nama_dok = "Esai Kandidat"
                if isinstance(pdf_path, str) and os.path.exists(pdf_path):
                    with st.expander(nama_dok):
                        with open(pdf_path, "rb") as f:
                            pdf_data = f.read()
                        base64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
                            f'width="100%" height="700" type="application/pdf"></iframe>',
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("Dokumen esai belum diupload oleh kandidat.")

            elif dm_key == "DM2_RencanaStudi":
                pdf_path = k.get("file_rencana_studi")
                nama_dok = "Rencana Studi"
                if isinstance(pdf_path, str) and os.path.exists(pdf_path):
                    with st.expander(nama_dok):
                        with open(pdf_path, "rb") as f:
                            pdf_data = f.read()
                        base64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
                            f'width="100%" height="700" type="application/pdf"></iframe>',
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("Dokumen rencana studi belum diupload oleh kandidat.")

            # Tampilkan info matching
            asesor_info = ASESOR_BY_ID.get(asesor_id, {})
            cocok = _bidang_cocok(prodi_k, asesor_info.get("bidang",""))
            if cocok:
                st.success(
                    f"Pencocokan berhasil: bidang Anda **{asesor_info.get('bidang','—')}** "
                    f"sesuai dengan prodi kandidat **{prodi_k}**"
                )
            else:
                st.info(
                    f"Pencocokan alternatif: bidang Anda **{asesor_info.get('bidang','—')}** "
                    f"| prodi kandidat **{prodi_k}**"
                )

            st.markdown("---")
            st.markdown("**Input Nilai (0–100):**")
            cols = st.columns(len(sks))
            new_scores = {}
            for i, k_info in enumerate(kriteria_list):
                with cols[i]:
                    new_scores[k_info["nama"]] = st.number_input(
                        k_info["nama"].replace("_"," "),
                        min_value=0, max_value=100,
                        value=int(ex.get(k_info["nama"], _default_nilai(kid, k_info["nama"]))),
                        step=1,
                        key=f"sc_{asesor_id}_{kid}_{k_info['nama']}",
                    )

            if st.button(
                f"Simpan Penilaian {kid}", key=f"save_{asesor_id}_{kid}",
                use_container_width=True
            ):
                for sk, val in new_scores.items():
                    save_score(dm_key, str(kid), sk, float(val))
                # Update status di assignments
                df_assign = load_asesor_assignments()
                mask = (df_assign["asesor_id"]==asesor_id) & \
                       (df_assign["kandidat_id"]==str(kid))
                df_assign.loc[mask, "status"] = "selesai"
                save_asesor_assignments(df_assign)
                st.success(f"Penilaian untuk **{nama_k}** berhasil disimpan!")
                st.rerun()

