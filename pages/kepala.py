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
                      save_score, load_admin_closed, save_admin_closed,
                      save_substansi_closed, save_penetapan_final)
from auth import verify_login
from algorithms import (topsis, borda_count, verifikasi_administrasi,
                        match_asesor_kandidat, get_asesor_kandidat,
                        get_dm_asesor_overview, _bidang_cocok,
                        get_kandidat_by_id, generate_new_id,
                        status_badge, all_asesor_selesai)
from utils import render_sidebar, init_state
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════
# HALAMAN: KEPALA PUSLAPDIK
# ═══════════════════════════════════════════════════════════════

def page_kepala():
    render_sidebar()
    st.title("Dashboard Kepala Puslapdik")

    records   = load_pendaftar()
    verif     = load_verifications()
    ids_lolos = [str(r["id"]) for r in records if verif.get(str(r["id"]))=="lolos"]
    nama_map  = {str(r["id"]): r.get("nama","—") for r in records}

    # Muat ulang cache dari file jika borda_done tapi cache kosong (misal setelah login ulang)
    if st.session_state.borda_done and not st.session_state.topsis_cache:
        path_seleksi = f"{BASE_DIR}/laporan_hasil_seleksi.csv"
        if os.path.exists(path_seleksi):
            df_cache = pd.read_csv(path_seleksi)
            df_cache["ID"] = df_cache["ID"].astype(str)
            # Rebuild ranking_final dari file
            if "Ranking Final" in df_cache.columns:
                ranking_final = pd.Series(
                    df_cache["Ranking Final"].values,
                    index=df_cache["ID"].values
                )
                borda_scores = pd.Series(
                    df_cache["Total Poin"].values,
                    index=df_cache["ID"].values,
                    dtype=float
                )
                st.session_state.topsis_cache = {
                    "skor":          {},
                    "ranking":       {},
                    "borda":         borda_scores,
                    "ranking_final": ranking_final,
                    "ids_lolos":     ids_lolos,
                    "nama_map":      nama_map,
                }

    tab1, tab2, tab3, tab4 = st.tabs([
        "Konfigurasi",
        "Progress Asesor",
        "Hasil Seleksi",
        "Penetapan Final",
    ])

    # ── Tab 1: Konfigurasi ────────────────────────────────────
    with tab1:
        st.subheader("Bobot Subkriteria per Kriteria")
        for dm_key, dm_val in KRITERIA_DM.items():
            st.markdown(f"##### {dm_val['label']}")
            st.dataframe(pd.DataFrame({
                "Subkriteria": [k["nama"].replace("_"," ") for k in dm_val["kriteria"]],
                "Bobot":       [f"{k['bobot']*100:.0f}%" for k in dm_val["kriteria"]],
                "Tipe":        [k["tipe"] for k in dm_val["kriteria"]],
            }), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Kuota & Asesor")
        c1, c2 = st.columns(2)
        c1.metric("Kuota Beasiswa", f"{KUOTA_BEASISWA} orang")
        c2.metric("Total Asesor", len(ASESOR_POOL))

    # ── Tab 2: Progress Asesor ────────────────────────────────
    with tab2:
        st.subheader("Progress Penilaian Asesor")

        if not st.session_state.admin_closed:
            st.warning("Tahap administrasi belum ditutup oleh Admin.")
        elif not ids_lolos:
            st.info("Belum ada kandidat yang lolos administrasi.")
        else:
            # Progress global
            total_penilaian   = 0
            selesai_penilaian = 0
            for dm_key, dm_val in KRITERIA_DM.items():
                sks = [k["nama"] for k in dm_val["kriteria"]]
                for kid in ids_lolos:
                    total_penilaian += 1
                    if all(sk in load_scores_kandidat(dm_key, kid) for sk in sks):
                        selesai_penilaian += 1

            st.progress(
                selesai_penilaian / total_penilaian if total_penilaian else 0,
                text=f"Total progress: {selesai_penilaian}/{total_penilaian} penilaian selesai"
            )

            with st.expander("Utilitas Demo — Auto-Isi Nilai Asesor"):
                st.caption("Isi semua nilai yang belum ada dengan skor acak realistis (60–100). "
                           "Gunakan hanya untuk keperluan demo.")
                import random
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Auto-Isi Semua Nilai Kosong",
                                 use_container_width=True):
                        filled = 0
                        for dm_key, dm_val in KRITERIA_DM.items():
                            sks = [k["nama"] for k in dm_val["kriteria"]]
                            for kid in ids_lolos:
                                nilai = load_scores_kandidat(dm_key, str(kid))
                                for sk in sks:
                                    if sk not in nilai:
                                        save_score(dm_key, str(kid), sk,
                                                   float(random.randint(60, 100)))
                                        filled += 1
                        st.success(f"{filled} nilai berhasil diisi!")
                        st.rerun()
                with col_b:
                    if st.button("Reset Semua Nilai",
                                 use_container_width=True):
                        import shutil
                        if os.path.exists(NILAI_DIR):
                            shutil.rmtree(NILAI_DIR)
                            os.makedirs(NILAI_DIR, exist_ok=True)
                        st.info("Semua nilai dihapus.")
                        st.rerun()

            st.markdown("---")

            for dm_key, dm_val in KRITERIA_DM.items():
                sks  = [k["nama"] for k in dm_val["kriteria"]]
                done = sum(1 for kid in ids_lolos
                           if all(sk in load_scores_kandidat(dm_key, kid) for sk in sks))

                with st.expander(
                    f"**{dm_val['label']}** — "
                    f"{done}/{len(ids_lolos)} kandidat selesai dinilai"
                ):
                    st.markdown("**Progress Asesor:**")
                    df_overview = get_dm_asesor_overview(dm_key)
                    if not df_overview.empty:
                        n_sel = (df_overview["Status Nilai"] == "Selesai").sum()
                        st.progress(n_sel / len(df_overview),
                                    text=f"{n_sel}/{len(df_overview)} asesor selesai")
                        st.dataframe(df_overview, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    st.markdown("**Detail Nilai per Kandidat:**")
                    rows_rekap = []
                    for kid in ids_lolos:
                        nilai = load_scores_kandidat(dm_key, str(kid))
                        row_r = {
                            "ID":     kid,
                            "Nama":   nama_map.get(kid, "—"),
                            "Status": "Selesai" if all(sk in nilai for sk in sks)
                                      else "Belum",
                        }
                        for sk in sks:
                            row_r[sk.replace("_", " ")] = (
                                f"{nilai[sk]:.0f}" if sk in nilai else "—"
                            )
                        rows_rekap.append(row_r)
                    st.dataframe(pd.DataFrame(rows_rekap),
                                 use_container_width=True, hide_index=True)

    # ── Tab 3: Hasil Seleksi ──────────────────────────────────
    with tab3:
        st.subheader("Hasil Seleksi Substansi")

        if not st.session_state.admin_closed:
            st.warning("Tahap administrasi belum ditutup oleh Admin.")
        elif not ids_lolos:
            st.warning("Tidak ada kandidat yang lolos administrasi.")
        else:
            if st.session_state.get("substansi_closed", False):
                st.success("Proses perhitungan substansi telah selesai.")
                path_seleksi = f"{BASE_DIR}/laporan_hasil_seleksi.csv"
                if os.path.exists(path_seleksi):
                    df_hasil = pd.read_csv(path_seleksi)

                    # Detail skor TOPSIS per DM
                    # Prioritas: dari cache (saat baru diproses)
                    # Fallback: baca kolom Skor & Rank dari CSV (setelah login ulang)
                    cache       = st.session_state.topsis_cache
                    skor_topsis = cache.get("skor", {})
                    ranking_top = cache.get("ranking", {})
                    nama_map_c  = cache.get("nama_map", nama_map)

                    with st.expander("Detail Skor TOPSIS per Kriteria"):
                        for dm_key, dm_val in KRITERIA_DM.items():
                            lbl = dm_val["label"].split("—")[1].strip()
                            st.markdown(f"##### {dm_val['label']}")

                            if skor_topsis and dm_key in skor_topsis:
                                # Dari cache (baru diproses)
                                ids_lolos_c = cache.get("ids_lolos", ids_lolos)
                                rows_show = [
                                    {
                                        "Rank":        int(ranking_top[dm_key][kid]),
                                        "ID":          kid,
                                        "Nama":        nama_map_c.get(kid, "—"),
                                        "Skor TOPSIS": f"{float(skor_topsis[dm_key][kid]):.4f}",
                                    }
                                    for kid in ids_lolos_c
                                    if kid in skor_topsis[dm_key].index
                                ]
                                rows_show.sort(key=lambda x: x["Rank"])
                                st.dataframe(pd.DataFrame(rows_show),
                                             use_container_width=True, hide_index=True)
                            else:
                                # Fallback: baca dari CSV
                                col_skor = f"Skor {lbl}"
                                col_rank = f"Rank {lbl}"
                                if col_skor in df_hasil.columns and col_rank in df_hasil.columns:
                                    df_show = df_hasil[["ID", "Nama", col_rank, col_skor]].copy()
                                    df_show = df_show.rename(columns={
                                        col_rank: "Rank",
                                        col_skor: "Skor TOPSIS",
                                    })
                                    df_show = df_show.sort_values("Rank")
                                    st.dataframe(df_show, use_container_width=True, hide_index=True)
                                else:
                                    st.caption("Detail skor tidak tersedia.")

                    st.markdown("#### Ranking Akhir Kandidat (TOPSIS + Borda Count)")
                    cols = ["Ranking Final"] + [c for c in df_hasil.columns if c != "Ranking Final"]
                    st.dataframe(df_hasil.sort_values("Ranking Final")[cols],
                                 use_container_width=True, hide_index=True)

                    csv_bytes = df_hasil.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Unduh Laporan Hasil Seleksi (CSV)",
                        data=csv_bytes,
                        file_name="laporan_hasil_seleksi.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            else:
                all_done = True
                for dm_key, dm_val in KRITERIA_DM.items():
                    sks  = [k["nama"] for k in dm_val["kriteria"]]
                    done = sum(1 for kid in ids_lolos
                               if all(sk in load_scores_kandidat(dm_key, kid) for sk in sks))
                    if done < len(ids_lolos):
                        all_done = False
                    st.markdown(
                        f"**{dm_val['label']}** — "
                        f"{done}/{len(ids_lolos)} kandidat selesai dinilai"
                    )

                st.markdown("---")

                if not all_done:
                    st.warning(
                        "Masih ada kandidat yang belum selesai dinilai. "
                        "Tunggu semua asesor selesai atau gunakan utilitas demo."
                    )

                if st.button(
                    "Proses Hasil Seleksi (TOPSIS + Borda Count)",
                    type="primary", use_container_width=True,
                    disabled=not all_done
                ):
                    skor_topsis    = {}
                    ranking_topsis = {}
                    with st.spinner("Memproses hasil seleksi..."):
                        for dm_key, dm_val in KRITERIA_DM.items():
                            df_mat = load_scores_all_dm(dm_key, ids_lolos)
                            sks    = [k["nama"] for k in dm_val["kriteria"]]
                            df_mat = df_mat[[c for c in sks if c in df_mat.columns]].dropna()
                            if df_mat.empty:
                                continue
                            skor = topsis(df_mat, dm_val["kriteria"])
                            rank = skor.rank(ascending=False, method="min").astype(int)
                            skor_topsis[dm_key]    = skor
                            ranking_topsis[dm_key] = rank

                    with st.spinner("Menyusun ranking akhir..."):
                        borda_scores  = borda_count(ranking_topsis, ids_lolos)
                        ranking_final = borda_scores.rank(ascending=False, method="min").astype(int)

                    df_tb = pd.DataFrame({"Total Poin": borda_scores})
                    for dm_key in ["DM3_Wawancara", "DM1_Esai", "DM2_RencanaStudi"]:
                        if dm_key in skor_topsis:
                            lbl = KRITERIA_DM[dm_key]["label"].split("—")[1].strip()
                            df_tb[f"Skor_{lbl}"] = skor_topsis[dm_key]
                    df_tb = df_tb.sort_values(
                        list(df_tb.columns), ascending=[False]*len(df_tb.columns)
                    )
                    df_tb["Ranking Final"] = range(1, len(df_tb)+1)
                    ranking_final = df_tb["Ranking Final"]

                    st.session_state.topsis_cache = {
                        "skor":          skor_topsis,
                        "ranking":       ranking_topsis,
                        "borda":         borda_scores,
                        "ranking_final": ranking_final,
                        "ids_lolos":     ids_lolos,
                        "nama_map":      nama_map,
                    }
                    st.session_state.borda_done       = True
                    st.session_state.substansi_closed = True

                    rows_sub = []
                    for kid in ids_lolos:
                        row_s = {"ID": kid, "Nama": nama_map.get(kid, "—")}
                        for dm_key, dm_val in KRITERIA_DM.items():
                            if dm_key in skor_topsis and kid in skor_topsis[dm_key].index:
                                lbl = dm_val["label"].split("—")[1].strip()
                                row_s[f"Skor {lbl}"] = round(float(skor_topsis[dm_key][kid]), 4)
                                row_s[f"Rank {lbl}"] = int(ranking_topsis[dm_key][kid])
                        row_s["Total Poin"]    = int(borda_scores.get(kid, 0))
                        row_s["Ranking Final"] = int(ranking_final.get(kid, 0))
                        rows_sub.append(row_s)

                    pd.DataFrame(rows_sub).sort_values("Ranking Final").to_csv(
                        f"{BASE_DIR}/laporan_hasil_seleksi.csv", index=False
                    )
                    save_substansi_closed()
                    st.success("Hasil seleksi berhasil diproses! Lanjut ke tab Penetapan Final.")
                    st.rerun()

    # ── Tab 4: Penetapan Final ────────────────────────────────
    with tab4:
        st.subheader("Penetapan Penerima Beasiswa")

        if not st.session_state.get("substansi_closed", False):
            st.info(
                "Proses hasil seleksi belum dijalankan. "
                "Silakan jalankan perhitungan di tab **Hasil Seleksi** terlebih dahulu."
            )

        elif st.session_state.get("penetapan_done", False):
            path_final = f"{BASE_DIR}/laporan_penetapan_final.csv"
            if os.path.exists(path_final):
                df_kep     = pd.read_csv(path_final)
                ditetapkan = df_kep[df_kep["Status Penetapan"].str.startswith("DITETAPKAN")]
                overridden = df_kep[df_kep["Status Penetapan"] == "OVERRIDE — DITOLAK"]

                st.success("Penetapan final telah selesai dan dikunci.")
                st.markdown(f"#### Penerima Beasiswa ({len(ditetapkan)} orang)")
                st.dataframe(ditetapkan, use_container_width=True, hide_index=True)
                if len(overridden) > 0:
                    st.markdown(f"#### Di-override ({len(overridden)} orang)")
                    st.dataframe(overridden, use_container_width=True, hide_index=True)

                st.markdown("---")
                c1, c2 = st.columns(2)
                c1.metric("Total Pendaftar",    len(records))
                c1.metric("Lolos Administrasi", len(ids_lolos))
                c2.metric("Ditetapkan",         len(ditetapkan))
                c2.metric("Di-override",        len(overridden))

                st.markdown("---")
                _tampilkan_rekap_kandidat(records, load_verifications(), path_final)

        else:
            cache         = st.session_state.topsis_cache
            skor_topsis   = cache.get("skor", {})
            ranking_top   = cache.get("ranking", {})
            borda_scores  = cache["borda"]
            ranking_final = cache["ranking_final"]
            ids_lolos_c   = cache["ids_lolos"]
            nama_map_c    = cache["nama_map"]

            rows_b = []
            for kid in borda_scores.sort_values(ascending=False).index:
                rb = {
                    "Ranking Final": int(ranking_final.get(kid, 0)),
                    "ID":            kid,
                    "Nama":          nama_map_c.get(kid, "—"),
                    "Total Poin":    int(borda_scores[kid]),
                }
                for dm_key, dm_val in KRITERIA_DM.items():
                    if dm_key in ranking_top and kid in ranking_top[dm_key].index:
                        lbl = dm_val["label"].split("—")[1].strip()
                        rb[f"Rank {lbl}"] = int(ranking_top[dm_key][kid])
                rows_b.append(rb)

            df_borda = pd.DataFrame(rows_b).sort_values("Ranking Final")
            df_borda.index = range(1, len(df_borda)+1)

            st.markdown(f"#### Ranking Akhir — Kuota: {KUOTA_BEASISWA} orang")
            st.dataframe(df_borda[df_borda["Ranking Final"] <= KUOTA_BEASISWA],
                         use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### Override Kepala Puslapdik")
            df_top = df_borda[df_borda["Ranking Final"] <= KUOTA_BEASISWA].copy()
            override_ranks = st.multiselect(
                "Pilih ranking yang akan di-override (ditolak/ditunda):",
                options=list(range(1, KUOTA_BEASISWA+1)),
            )
            override_alasan = {}
            for rv in override_ranks:
                override_alasan[rv] = st.text_input(
                    f"Alasan override ranking #{rv}:",
                    key=f"alasan_{rv}",
                    placeholder="Contoh: conflict of interest",
                )

            if st.button("Tetapkan & Simpan Laporan Final",
                         type="primary", use_container_width=True):
                df_pen = df_top.copy()
                df_pen["Status Penetapan"] = "DITETAPKAN"
                df_pen["Catatan Kepala"]   = "Setuju — sesuai ranking"
                for rv in override_ranks:
                    mask = df_pen["Ranking Final"] == rv
                    df_pen.loc[mask, "Status Penetapan"] = "OVERRIDE — DITOLAK"
                    df_pen.loc[mask, "Catatan Kepala"]   = (
                        f"Tidak setuju — {override_alasan.get(rv, '-')}"
                    )
                n_ov    = len(override_ranks)
                df_peng = df_borda[df_borda["Ranking Final"] > KUOTA_BEASISWA].head(n_ov).copy()
                df_peng["Status Penetapan"] = "DITETAPKAN (Pengganti)"
                df_peng["Catatan Kepala"]   = "Masuk sebagai pengganti"

                df_kep = pd.concat([df_pen, df_peng], ignore_index=True)
                df_kep = df_kep.sort_values(["Status Penetapan", "Ranking Final"])
                df_kep.index = range(1, len(df_kep)+1)
                df_kep.to_csv(f"{BASE_DIR}/laporan_penetapan_final.csv", index=False)

                save_penetapan_final()
                st.session_state.penetapan_done = True
                st.success("Laporan final tersimpan dan proses penetapan dikunci!")
                st.rerun()


def _tampilkan_rekap_kandidat(records, verif, path_final):
    """Rekap seluruh kandidat — ditampilkan setelah penetapan final selesai."""
    df_final = pd.DataFrame()
    if os.path.exists(path_final):
        df_final = pd.read_csv(path_final)
        df_final["ID"] = df_final["ID"].astype(str)

    rows_rekap = []
    for r in records:
        kid      = str(r.get("id", ""))
        st_verif = verif.get(kid, "pending")
        lengkap  = str(r.get("pendaftaran_lengkap", "False")).lower() in ("true","1")

        if not lengkap:
            status_akhir = "Belum Submit Formulir"
        elif st_verif == "pending":
            status_akhir = "Menunggu Verifikasi Admin"
        elif st_verif == "lolos_auto":
            status_akhir = "Menunggu Verifikasi Dokumen"
        elif st_verif == "tidak_lolos":
            status_akhir = "Tidak Lolos Administrasi"
        elif st_verif == "lolos":
            if df_final.empty:
                status_akhir = "Tidak Lolos — Tidak Masuk Kuota"
            else:
                row_f = df_final[df_final["ID"] == kid]
                if row_f.empty:
                    status_akhir = "Tidak Lolos — Tidak Masuk Kuota"
                else:
                    stat_p = str(row_f.iloc[0].get("Status Penetapan", ""))
                    if stat_p.startswith("DITETAPKAN"):
                        status_akhir = "Lolos — Ditetapkan Penerima Beasiswa"
                    else:
                        status_akhir = "Tidak Lolos Beasiswa Unggulan"
        else:
            status_akhir = st_verif

        rows_rekap.append({
            "ID":           kid,
            "Nama":         r.get("nama", "—"),
            "Universitas":  r.get("universitas", "—"),
            "Prodi":        r.get("prodi", "—"),
            "IPK":          r.get("ipk", "—"),
            "Status Akhir": status_akhir,
        })

    df_rekap = pd.DataFrame(rows_rekap)
    st.markdown("#### Rekap Seluruh Kandidat")

    filter_status = st.selectbox(
        "Filter Status:",
        ["Semua"] + sorted(df_rekap["Status Akhir"].unique().tolist()),
        key="filter_rekap"
    )
    df_tampil = df_rekap if filter_status == "Semua" \
                else df_rekap[df_rekap["Status Akhir"] == filter_status]

    st.dataframe(df_tampil, use_container_width=True, hide_index=True)
    st.caption(f"Menampilkan {len(df_tampil)} dari {len(records)} kandidat")

    csv_rekap = df_rekap.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Unduh Rekap Semua Kandidat (CSV)",
        data=csv_rekap,
        file_name="rekap_semua_kandidat.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_rekap_kandidat",
    )