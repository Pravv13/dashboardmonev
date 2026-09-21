import streamlit as st
import pandas as pd
import tempfile
import os
import io
import plotly.express as px
import plotly.graph_objects as go
from validasi_cst01 import bersihkan_dan_validasi_laporan, baca_file_otomatis

# ==========================================
# 1. KONFIGURASI HALAMAN & STATE
# ==========================================
st.set_page_config(page_title="ETL Data Pendampingan", page_icon="🧩", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stMetric"] { 
        background-color: var(--secondary-background-color); 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Session State
if 'df_hasil' not in st.session_state:
    st.session_state.df_hasil = None
if 'total_baris_data' not in st.session_state:
    st.session_state.total_baris_data = 0

# ==========================================
# 2. SIDEBAR: KONTROL & UPLOAD
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/id/0/03/Lambang_Universitas_Tanjungpura.png", width=90)
    st.title("Parameter ETL")
    st.markdown("Sistem *Rule-Based* CST-01 & NP-03")
    st.divider()

    file_cst = st.file_uploader("📂 1. Unggah Data CST-01", type=['xlsx', 'xls', 'xlsb', 'csv'])
    file_np = st.file_uploader("📂 2. Unggah Data NP-03", type=['xlsx', 'xls', 'xlsb', 'csv'])
    file_petugas = st.file_uploader("📂 3. Unggah Master Data Petugas", type=['xlsx', 'xls', 'xlsb', 'csv'])

    st.divider()
    btn_proses = st.button("🚀 Eksekusi Pipeline ETL", use_container_width=True, type="primary")

    if st.button("🔄 Reset Data", use_container_width=True):
        st.session_state.df_hasil = None
        st.session_state.total_baris_data = 0
        st.rerun()

# ==========================================
# 3. AREA UTAMA (MAIN DASHBOARD)
# ==========================================
st.title("🧩 Dashboard Data Quality Assurance (DQA)")
st.caption("Mendukung Otomatisasi Penjaminan Mutu Data Layanan Medis melalui Pendekatan Rule-Based System")

if not file_cst or not file_np or not file_petugas:
    st.info(
        "👋 Selamat datang! Silakan unggah dokumen CST-01, NP-03, beserta Data Petugas pada panel sebelah kiri untuk memulai proses ekstraksi dan validasi.")

# ==========================================
# 4. PROSES ETL, VLOOKUP & REGEX EXTRACTION
# ==========================================
if btn_proses and file_cst and file_np and file_petugas:
    with st.spinner("Memproses data... Mengekstrak logika temporal, wilayah, dan petugas..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_cst:
            tmp_cst.write(file_cst.getvalue())
            cst_path = tmp_cst.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_np:
            tmp_np.write(file_np.getvalue())
            np_path = tmp_np.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_petugas:
            tmp_petugas.write(file_petugas.getvalue())
            petugas_path = tmp_petugas.name

        try:
            # A. Eksekusi proses ETL Backend
            hasil_error = bersihkan_dan_validasi_laporan(cst_path, np_path)

            data_rekap = []
            for rule, list_pesan in hasil_error.items():
                for pesan in list_pesan:
                    data_rekap.append({"Kategori Aturan (Rule)": rule, "Deskripsi Anomali": pesan})

            df_hasil = pd.DataFrame(data_rekap)

            # B. Baca Raw Data untuk VLOOKUP & Metrik
            df_cst_raw = baca_file_otomatis(cst_path)
            df_np_raw = baca_file_otomatis(np_path)

            # Hitung total baris untuk Health Score
            st.session_state.total_baris_data = len(df_cst_raw) + len(df_np_raw)

            # C. LOGIC PENCOCOKAN (Frontend BI Processing)
            if not df_hasil.empty:
                # 1. Ekstrak ID Klien & Tanggal via Regex
                df_hasil['ID Klien'] = df_hasil['Deskripsi Anomali'].str.extract(r'Klien\s([A-Za-z0-9]+)', expand=False)
                df_hasil['Tanggal Laporan'] = df_hasil['Deskripsi Anomali'].str.extract(
                    r'Laporan:\s(\d{4}-\d{2}-\d{2})', expand=False)
                df_hasil['Tanggal Laporan'] = pd.to_datetime(df_hasil['Tanggal Laporan'], errors='coerce')

                # 2. VLOOKUP Petugas & Wilayah dari CST
                col_id_cst = next((c for c in df_cst_raw.columns if 'id klien' in str(c).lower()), 'ID Klien')
                col_kode_cst = next((c for c in df_cst_raw.columns if 'kode petugas' in str(c).lower()), 'Kode Petugas')
                col_kab_cst = next(
                    (c for c in df_cst_raw.columns if 'kabupaten' in str(c).lower() or 'kota' in str(c).lower()),
                    'Kabupaten/Kota')

                if col_id_cst in df_cst_raw.columns:
                    # Ambil Kode Petugas & Kabupaten
                    cols_to_extract = [col_id_cst]
                    if col_kode_cst in df_cst_raw.columns: cols_to_extract.append(col_kode_cst)
                    if col_kab_cst in df_cst_raw.columns: cols_to_extract.append(col_kab_cst)

                    df_mapping = df_cst_raw[cols_to_extract].drop_duplicates(subset=[col_id_cst])
                    df_hasil = pd.merge(df_hasil, df_mapping, left_on='ID Klien', right_on=col_id_cst, how='left')

                    if col_kode_cst in df_hasil.columns: df_hasil.rename(columns={col_kode_cst: 'Kode Petugas'},
                                                                         inplace=True)
                    if col_kab_cst in df_hasil.columns: df_hasil.rename(columns={col_kab_cst: 'Wilayah (Kab/Kota)'},
                                                                        inplace=True)

                # 3. VLOOKUP Nama Petugas dari Master Petugas
                df_petugas = baca_file_otomatis(petugas_path)
                col_kode_master = next((c for c in df_petugas.columns if 'kode' in str(c).lower()), 'Kode Petugas')
                col_nama_master = next((c for c in df_petugas.columns if 'nama' in str(c).lower()), 'Nama Petugas')

                if col_kode_master in df_petugas.columns and 'Kode Petugas' in df_hasil.columns:
                    df_hasil = pd.merge(df_hasil, df_petugas[[col_kode_master, col_nama_master]],
                                        left_on='Kode Petugas', right_on=col_kode_master, how='left')
                    df_hasil.rename(columns={col_nama_master: 'Nama Petugas'}, inplace=True)

                # 4. Susun ulang kolom
                kolom_tampil = ['Kategori Aturan (Rule)', 'Tanggal Laporan', 'Wilayah (Kab/Kota)', 'ID Klien',
                                'Nama Petugas', 'Deskripsi Anomali']
                kolom_tersedia = [k for k in kolom_tampil if k in df_hasil.columns]
                sisa_kolom = [c for c in df_hasil.columns if
                              c not in kolom_tersedia and c not in ['Kode Petugas', col_id_cst]]
                df_hasil = df_hasil[kolom_tersedia + sisa_kolom]

            # D. Bersihkan file temp dari server
            os.remove(cst_path)
            os.remove(np_path)
            os.remove(petugas_path)

            st.session_state.df_hasil = df_hasil

        except Exception as e:
            st.error(f"FATAL ERROR: Terjadi kegagalan pada pipeline pemrosesan. Rincian: {e}")

# ==========================================
# 5. TATA LETAK MULTI-TAB (EXECUTIVE VIEW)
# ==========================================
if st.session_state.df_hasil is not None:
    df_hasil = st.session_state.df_hasil

    if df_hasil.empty:
        st.success("🎉 Sempurna! Data valid dan tersinkronisasi 100%. Tidak ditemukan pelanggaran logika.")
    else:
        tab1, tab2, tab3 = st.tabs(
            ["📊 Executive Summary", "📈 Analisis Visual Mendalam", "🗃️ Eksplorasi Data & Unduhan"])

        # --- TAB 1: EXECUTIVE SUMMARY (HEALTH SCORE & PIE CHART) ---
        with tab1:
            st.subheader("Ringkasan Eksekutif Temuan Anomali")

            total_anomali = len(df_hasil)
            aturan_unik = df_hasil['Kategori Aturan (Rule)'].nunique()
            rule_terbanyak = df_hasil['Kategori Aturan (Rule)'].mode()[0]

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric(label="Total Temuan Anomali", value=f"{total_anomali} Kasus", delta="Dari total baris data",
                        delta_color="inverse")
            kpi2.metric(label="Jumlah Rule Dilanggar", value=f"{aturan_unik} Rule", delta="Dari Total 27 Aturan",
                        delta_color="off")
            kpi3.metric(label="Aturan Paling Rentan", value=rule_terbanyak.split(":")[0], delta="Perlu peninjauan",
                        delta_color="inverse")

            st.markdown("---")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.write("**Data Health Score (Indeks Mutu Data)**")
                # Kalkulasi Data Health Score
                total_baris = st.session_state.total_baris_data
                skor_kesehatan = max(0, 100 - (total_anomali / total_baris * 100)) if total_baris > 0 else 0

                # PERBAIKAN SPIDOMETER (Desain Clean & Adaptif Dark Mode)
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=skor_kesehatan,
                    title={'text': "Kualitas Data (%)", 'font': {'size': 18}},
                    # Warna font dihapus agar Streamlit otomatis memberikan warna kontras (putih di dark mode)
                    number={'suffix': "%", 'font': {'size': 42}},
                    gauge={
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                        'bgcolor': "rgba(0,0,0,0)",
                        # Warna bar dibuat lebih cerah (Neon Green/Yellow/Red) biar "pop-up"
                        'bar': {'color': "#00E676" if skor_kesehatan >= 90 else (
                            "#FFD600" if skor_kesehatan >= 75 else "#FF1744")},
                        'steps': [
                            # Track background disatukan jadi satu warna abu-abu transparan biar rapi
                            {'range': [0, 100], 'color': "rgba(128, 128, 128, 0.2)"}
                        ],
                        'threshold': {
                            'line': {'color': "#FF1744", 'width': 4},
                            'thickness': 0.75,
                            'value': 90  # Garis target kualitas 90%
                        }
                    }
                ))
                fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
                # Parameter theme="streamlit" memaksa grafik membaur sempurna dengan tema bawaan
                st.plotly_chart(fig_gauge, use_container_width=True, theme="streamlit")

            with col_chart2:
                st.write("**Komposisi Pelanggaran Data**")
                df_pie = df_hasil['Kategori Aturan (Rule)'].value_counts().reset_index()
                df_pie.columns = ['Rule', 'Jumlah']
                df_pie.loc[df_pie['Jumlah'] < (total_anomali * 0.05), 'Rule'] = 'Lainnya (<5%)'
                fig_pie = px.pie(df_pie, values='Jumlah', names='Rule', hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

        # --- TAB 2: ANALISIS VISUAL (TREN, WILAYAH, PETUGAS) ---
        with tab2:
            st.subheader("📈 Analisis Tren Waktu Anomali")
            if 'Tanggal Laporan' in df_hasil.columns and not df_hasil['Tanggal Laporan'].isna().all():
                df_tren = df_hasil.groupby(df_hasil['Tanggal Laporan'].dt.date).size().reset_index(
                    name='Jumlah Anomali')
                fig_line = px.line(df_tren, x='Tanggal Laporan', y='Jumlah Anomali', markers=True,
                                   color_discrete_sequence=['#E91E63'])
                fig_line.update_layout(xaxis_title="Tanggal Laporan", yaxis_title="Total Anomali", height=350)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Tidak ada data tanggal yang dapat diekstrak secara otomatis untuk analisis tren waktu.")

            st.markdown("---")
            col_analisis1, col_analisis2 = st.columns(2)

            with col_analisis1:
                st.subheader("🗺️ Top Wilayah Penyumbang Anomali")
                if 'Wilayah (Kab/Kota)' in df_hasil.columns:
                    df_wilayah = df_hasil['Wilayah (Kab/Kota)'].fillna('Tidak Diketahui').value_counts().reset_index()
                    df_wilayah.columns = ['Wilayah', 'Jumlah']

                    # PERBAIKAN: Tambah Data Label
                    fig_wil = px.bar(df_wilayah.head(10), x='Jumlah', y='Wilayah', orientation='h', color='Jumlah',
                                     color_continuous_scale='Blues', text='Jumlah')
                    fig_wil.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400, showlegend=False)
                    fig_wil.update_traces(textposition='outside', textfont_size=13)  # Teks di luar batang
                    st.plotly_chart(fig_wil, use_container_width=True)
                else:
                    st.info("Data Wilayah tidak tersedia.")

            with col_analisis2:
                st.subheader("👥 Analisis Kinerja Petugas")
                if 'Nama Petugas' in df_hasil.columns:
                    df_petugas = df_hasil['Nama Petugas'].fillna(
                        'Tidak Diketahui / Kode Tidak Valid').value_counts().reset_index()
                    df_petugas.columns = ['Nama Petugas', 'Jumlah']

                    batas_tampil = st.selectbox("Pilih Tampilan Petugas:", ["Top 5", "Top 10", "Top 20", "Semua"],
                                                index=1, key="filter_petugas")
                    df_ptg_tampil = df_petugas if batas_tampil == "Semua" else df_petugas.head(
                        int(batas_tampil.split(" ")[1]))

                    # PERBAIKAN: Tambah Data Label
                    fig_petugas = px.bar(df_ptg_tampil, x='Jumlah', y='Nama Petugas', orientation='h', color='Jumlah',
                                         color_continuous_scale='Oranges', text='Jumlah')
                    fig_petugas.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400, showlegend=False)
                    fig_petugas.update_traces(textposition='outside', textfont_size=13)  # Teks di luar batang
                    st.plotly_chart(fig_petugas, use_container_width=True)
                else:
                    st.info("Data Petugas tidak tersedia.")

        # --- TAB 3: EKSPLORASI DATA & EXPORT ---
        with tab3:
            st.subheader("Tabel Anomali Interaktif")

            col_filter1, col_filter2 = st.columns([1, 2])
            with col_filter1:
                pilihan_rule = ["Tampilkan Semua Kategori"] + list(df_hasil['Kategori Aturan (Rule)'].unique())
                filter_rule = st.selectbox("🎯 Filter Berdasarkan Rule:", pilihan_rule)
            with col_filter2:
                pencarian = st.text_input("🔍 Cari Spesifik (Misal: ketik ID Klien, NIK, Kota, atau Nama):")

            # Terapkan Filter
            df_tampil = df_hasil.copy()
            if filter_rule != "Tampilkan Semua Kategori":
                df_tampil = df_tampil[df_tampil['Kategori Aturan (Rule)'] == filter_rule]
            if pencarian:
                mask = df_tampil.astype(str).apply(lambda x: x.str.contains(pencarian, case=False, na=False)).any(
                    axis=1)
                df_tampil = df_tampil[mask]

            st.dataframe(df_tampil, use_container_width=True, height=400)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_tampil.to_excel(writer, index=False, sheet_name='Rekap Anomali')
            excel_data = output.getvalue()

            st.download_button(
                label="📥 Unduh Laporan Tabel Saat Ini (.xlsx)",
                data=excel_data,
                file_name="Laporan_Quality_Assurance_Medis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )