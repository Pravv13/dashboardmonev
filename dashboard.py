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

if 'df_hasil' not in st.session_state:
    st.session_state.df_hasil = None
if 'total_baris_data' not in st.session_state:
    st.session_state.total_baris_data = 0
if 'capaian_layanan' not in st.session_state:
    st.session_state.capaian_layanan = {"psiko": 0, "on_art": 0, "lfu": 0, "non_art": 0}


# ==========================================
# 1.5 MODAL PANDUAN PENGGUNA
# ==========================================
@st.dialog("📖 Panduan Ringkas: 27 Logika Validasi", width="large")
def tampilkan_panduan():
    st.markdown(
        "Sistem validasi otomatis akan membaca data Anda layaknya sebuah cerita dari waktu ke waktu. Agar laporan lolos tanpa error, berikut adalah 27 hal yang dicek otomatis:")

    with st.expander("A. CEK IDENTITAS (KTP & KODE) - [CST-01]"):
        st.markdown("""
        1. **ID Klien Standar**: Panjang wajib 10 atau 12 digit. Jika 11 digit, ujungnya hanya boleh huruf A atau B.
        2. **NIK Wajib Valid**: NIK mutlak harus 16 digit dan angka ujungnya tidak mungkin "000".
        3. **Anti NIK Silang**: 1 ID Klien hanya boleh punya 1 NIK. Begitu juga sebaliknya, 1 NIK tidak boleh dipakai oleh lebih dari 1 ID Klien (tidak boleh bentrok).
        """)

    with st.expander("B. CEK KEWAJARAN DATA (KROSCEK KOLOM) - [CST-01]"):
        st.markdown("""
        4. **Batasan Umur Anak**: Jika Tipe Klien adalah "Anak" (kode 9100), umurnya otomatis tidak boleh 18 tahun ke atas.
        5. **Tanggal Input Valid**: Tanggal Input laporan di sistem tidak boleh tercatat lebih dulu (mendahului) daripada Tanggal Kontak aktualnya.
        6. **Wajib Tipe Anak**: Sebaliknya, jika umurnya di bawah 18 tahun, Tipe Klien wajib diisi "Anak" (kode 9100).
        7. **Mesin Waktu**: Tanggal kontak klien tidak boleh lebih dulu (lebih tua) daripada Tanggal Tahu Status HIV.
        8. **Layanan ART Tidak Boleh Kosong**: Jika klien berstatus ART 0, 1, 2, 3, atau 4, nama puskesmas/RS tempat dia ambil obat mutlak wajib diisi. (Berfungsi juga untuk melacak faskes awal reaktif saat ART 0).
        9. **Sinkronisasi VO**: Jika Jenis Kegiatan diisi 4, kolom Lokasi wajib mengandung kata "VO". Sebaliknya, jika Lokasi mengandung "VO", Jenis Kegiatan wajib 4.
        10. **Inisiasi ART Wajib Jenis Kegiatan 2**: Jika klien baru mulai/inisiasi pengobatan (Status ART diisi angka 1), maka Jenis Kegiatan mutlak wajib diisi kode 2.
        11. **Status ART/LFU di Tanggal Tahu Status**: Jika baris laporan memiliki Tanggal Kontak yang sama persis dengan Tanggal Tahu Status, kondisinya dikunci. Klien hanya boleh berstatus ART 0 LFU 0 atau ART 1 LFU 0.
        12. **Inisiasi ART Wajib Rujukan Keluar 5/6**: Jika klien berstatus ART 1 (Inisiasi Terapi), kolom "Rujukan Keluar" wajib memuat kode 5 atau 6.
        """)

    with st.expander("C. CEK RIWAYAT PENGOBATAN (MAJU-MUNDUR) - [CST-01]"):
        st.markdown("""
        13. **Pantang Mundur ke ART 0**: Jika di laporan kontak sebelumnya klien sudah inisiasi mulai obat (ART 1/2/3/4), statusnya tidak boleh tiba-tiba mundur jadi ART 0 (Belum Terapi).
        14. **Syarat Putus Obat (LFU 1)**: Klien baru sah dicatat putus obat (LFU 1) kalau jarak dari terakhir kali dia aktif berobat sudah lewat dari 60 hari.
        15. **Validasi Riwayat LFU 2 (Dinamis)**: LFU 2 wajib didahului oleh ART 3 LFU 1. Jika sudah masuk LFU 2, tidak boleh mendadak ditarik kembali ke LFU 0 di semester yang sama.
        16. **Filter Pertama LFU 2 Anti ART 2**: Ketika klien baru memasuki siklus LFU 2 setelah putus obat, baris pertamanya pantang langsung melompat ke status ART 2 (Wajib diawali ART 1 terlebih dahulu).
        17. **Inisiasi ART Ganda**: Klien tidak boleh tercatat melakukan Inisiasi ART perdana (ART 1 LFU 0) lebih dari satu kali di dalam riwayat laporannya.
        18. **Rentang LFU Back ART**: Inisiasi kembali setelah LFU (ART 1 LFU 2) boleh tercatat lebih dari satu kali, JIKA DAN HANYA JIKA jarak dari riwayat ART 1 LFU 2 sebelumnya sudah lewat dari 60 hari.
        """)

    with st.expander("D. CEK LOGIKA TES & INTEGRASI SILANG - [NP-03]"):
        st.markdown("""
        19. **Syarat Wajib VCT**: Jika Hasil Tes HIV diisi (selain kosong atau opsi 3), maka kolom "Menerima Hasil VCT" mutlak wajib diisi angka 1 (Menerima).
        20. **Larangan Isi Tes HIV**: Sebaliknya, jika klien berstatus tidak menerima hasil VCT (bukan 1), maka Hasil Tes HIV tidak logis jika terisi (harus kosong atau diisi 3).
        21. **Sinkronisasi Klien Reaktif**: Jika klien dinyatakan Reaktif (1) di NP-03, identitasnya (ID Klien & NIK) wajib terdaftar dan sama persis dengan yang ada di file CST-01.
        22. **Kontak Perdana Wajib Sinkron**: Klien yang reaktif di NP-03 wajib memiliki rekam jejak pendampingan di CST-01 pada tanggal yang SAMA PERSIS dengan "Tanggal Tes HIV".
        23. **Status Pengobatan Awal**: Pada tanggal klien reaktif tersebut, riwayat pengobatan pertamanya di CST-01 hanya boleh berstatus ART 0 (Belum Terapi) atau ART 1 (Mulai Terapi).
        """)

    with st.expander("E. KETAHANAN SISTEM, WILAYAH KERJA, & PR-EP"):
        st.markdown("""
        24. **Smart Detection & Anti-Crash**: Sistem kebal terhadap salah ejaan/huruf besar/kecil di nama kolom Excel.
        25. **Kesesuaian Wilayah Intervensi IU**: Memvalidasi silang isi kolom IU (Implementing Unit) dan Kabupaten/Kota baik pada file CST-01 maupun NP-03 dengan database internal 20 lembaga resmi.
        26. **Reaktif Anti PrEP**: Jika Hasil Tes HIV klien dinyatakan Reaktif (1), maka klien tersebut tidak boleh tercatat "Menerima Obat PrEP" (karena PrEP hanya untuk pencegahan bagi yang negatif).
        27. **Non-Reaktif & N/A Anti CST**: Jika Hasil tes dinyatakan Non-Reaktif (2) atau status tesnya kosong/N/A, ID Klien tersebut pantang ditemukan masuk ke dalam data pengobatan HIV (CST-01).
        """)

# ==========================================
# 2. SIDEBAR: KONTROL & UPLOAD
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/id/0/03/Lambang_Universitas_Tanjungpura.png?utm_source=id.wikipedia.org&utm_campaign=index&utm_content=thumbnail_unscaled&_=20231211202742", width=90)
    st.title("Parameter ETL")
    st.markdown("Sistem *Rule-Based* CST-01 & NP-03")
    # Tambahkan ini di bawah teks deskripsi sidebar
    if st.button("📖 Lihat Panduan Validasi", use_container_width=True):
        tampilkan_panduan()
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
# 3. KONEKSI GOOGLE SHEETS API
# ==========================================
@st.cache_resource
def init_gsheets():
    try:
        import gspread
        import json
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Cek apakah dijalankan di Streamlit Cloud (via Secrets) atau di lokal
        if "gcp_credentials" in st.secrets:
            creds_dict = json.loads(st.secrets["gcp_credentials"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)

        client = gspread.authorize(creds)
        return client.open("Database Whitelist DQA").worksheet("Whitelist")
    except Exception as e:
        return None


sheet_db = init_gsheets()

# ==========================================
# 4. AREA UTAMA & PROSES ETL
# ==========================================
st.title("🧩 Dashboard Data Quality Assurance (DQA)")
st.caption("Mendukung Otomatisasi Penjaminan Mutu Data Layanan Medis melalui Pendekatan Rule-Based System")

if not file_cst or not file_np or not file_petugas:
    st.info(
        "👋 Selamat datang! Silakan unggah dokumen CST-01, NP-03, beserta Data Petugas pada panel sebelah kiri untuk memulai proses ekstraksi dan validasi.")

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
            # A. ETL Backend
            hasil_error = bersihkan_dan_validasi_laporan(cst_path, np_path)
            data_rekap = [{"Kategori Aturan (Rule)": rule, "Deskripsi Anomali": pesan} for rule, list_pesan in
                          hasil_error.items() for pesan in list_pesan]
            df_hasil = pd.DataFrame(data_rekap)

            # B. Metrik Total Baris & Capaian Layanan (Mimikri Excel Presisi Tinggi)
            df_cst_raw = baca_file_otomatis(cst_path)
            df_np_raw = baca_file_otomatis(np_path)
            st.session_state.total_baris_data = len(df_cst_raw) + len(df_np_raw)

            # Hitung Capaian Layanan dari CST-01
            kolom_cst = df_cst_raw.columns.tolist()

            # Cari nama kolom yang tepat berdasarkan struktur header Excel
            col_id = next((c for c in kolom_cst if 'id klien' in str(c).lower()), None)
            col_status = next((c for c in kolom_cst if 'status pengobatan' in str(c).lower()), None)
            col_tgl = next((c for c in kolom_cst if str(c).strip().lower() == 'tanggal'), None)

            if col_id and col_status:
                df_bersih = df_cst_raw.copy()

                # 1. BUANG BARIS SUB-HEADER (Baris ke-2 di Excel yang isinya "ART", "OAT", dll)
                if df_bersih[col_status].astype(str).str.strip().iloc[0] == 'ART':
                    df_bersih = df_bersih.iloc[1:]

                # 2. BERSIHKAN ID KLIEN
                df_bersih = df_bersih.dropna(subset=[col_id])
                df_bersih['ID_CLEAN'] = df_bersih[col_id].astype(str).str.strip().str.upper()
                df_bersih = df_bersih[
                    (df_bersih['ID_CLEAN'] != '') &
                    (df_bersih['ID_CLEAN'] != 'NAN') &
                    (~df_bersih['ID_CLEAN'].str.contains('TOTAL|JUMLAH', na=False))
                    ]

                # 3. SORT NEWEST TO OLDEST (MIMIKRI EXCEL STABLE SORT)
                if col_tgl:
                    # Simpan urutan baris asli sebagai penentu jika ada 2 data di tanggal yang sama
                    df_bersih['urutan_asli'] = range(len(df_bersih))
                    df_bersih['TGL_PARSE'] = pd.to_datetime(df_bersih[col_tgl], errors='coerce', dayfirst=True)
                    # Sort by Tanggal (Terbaru dulu), lalu berdasarkan urutan asli Excel (Atas ke Bawah)
                    df_bersih = df_bersih.sort_values(by=['TGL_PARSE', 'urutan_asli'], ascending=[False, True])

                # 4. REMOVE DUPLICATE (Ambil data paling atas sesuai logika Excel)
                df_unik = df_bersih.drop_duplicates(subset=['ID_CLEAN'], keep='first')

                # 5. HITUNG STATUS DARI KOLOM "ART" UTAMA
                status_asli = df_unik[col_status].astype(str).str.strip().str.replace('.0', '', regex=False)

                on_art = int(status_asli.isin(['1', '2', '4']).sum())
                lfu = int(status_asli.isin(['3']).sum())
                non_art = int(status_asli.isin(['0']).sum())

                # Rumus Psikososial = Jumlah total status yang valid
                psiko = on_art + lfu + non_art

                st.session_state.capaian_layanan = {
                    "psiko": psiko,
                    "on_art": on_art,
                    "lfu": lfu,
                    "non_art": non_art
                }
            else:
                st.warning(f"⚠️ Kolom tidak ditemukan! Daftar kolom: {', '.join(df_cst_raw.columns.astype(str))}")

            # C. VLOOKUP Logic
            if not df_hasil.empty:
                df_hasil['ID Klien'] = df_hasil['Deskripsi Anomali'].str.extract(r'Klien\s([A-Za-z0-9]+)', expand=False)
                df_hasil['Tanggal Laporan'] = pd.to_datetime(
                    df_hasil['Deskripsi Anomali'].str.extract(r'Laporan:\s(\d{4}-\d{2}-\d{2})', expand=False),
                    errors='coerce')

                col_id_cst = next((c for c in df_cst_raw.columns if 'id klien' in str(c).lower()), 'ID Klien')
                col_kode_cst = next((c for c in df_cst_raw.columns if 'kode petugas' in str(c).lower()), 'Kode Petugas')
                col_kab_cst = next(
                    (c for c in df_cst_raw.columns if 'kabupaten' in str(c).lower() or 'kota' in str(c).lower()),
                    'Kabupaten/Kota')
                col_lembaga = 'Lembaga'  # Kolom statis sesuai arahan lu

                if col_id_cst in df_cst_raw.columns:
                    cols_to_extract = [col_id_cst]
                    if col_kode_cst in df_cst_raw.columns: cols_to_extract.append(col_kode_cst)
                    if col_kab_cst in df_cst_raw.columns: cols_to_extract.append(col_kab_cst)
                    if col_lembaga in df_cst_raw.columns: cols_to_extract.append(col_lembaga)

                    df_mapping = df_cst_raw[cols_to_extract].drop_duplicates(subset=[col_id_cst])
                    df_hasil = pd.merge(df_hasil, df_mapping, left_on='ID Klien', right_on=col_id_cst, how='left')

                    if col_kode_cst in df_hasil.columns: df_hasil.rename(columns={col_kode_cst: 'Kode Petugas'},
                                                                         inplace=True)
                    if col_kab_cst in df_hasil.columns: df_hasil.rename(columns={col_kab_cst: 'Wilayah (Kab/Kota)'},
                                                                        inplace=True)

                df_petugas = baca_file_otomatis(petugas_path)
                col_kode_master = next((c for c in df_petugas.columns if 'kode' in str(c).lower()), 'Kode Petugas')
                col_nama_master = next((c for c in df_petugas.columns if 'nama' in str(c).lower()), 'Nama Petugas')

                if col_kode_master in df_petugas.columns and 'Kode Petugas' in df_hasil.columns:
                    df_hasil = pd.merge(df_hasil, df_petugas[[col_kode_master, col_nama_master]],
                                        left_on='Kode Petugas', right_on=col_kode_master, how='left')
                    df_hasil.rename(columns={col_nama_master: 'Nama Petugas'}, inplace=True)

                # Pastikan 'Lembaga' masuk di kolom tampil
                kolom_tampil = ['Kategori Aturan (Rule)', 'Tanggal Laporan', 'Wilayah (Kab/Kota)', 'Lembaga',
                                'ID Klien', 'Nama Petugas', 'Deskripsi Anomali']
                kolom_tersedia = [k for k in kolom_tampil if k in df_hasil.columns]
                df_hasil = df_hasil[kolom_tersedia + [c for c in df_hasil.columns if
                                                      c not in kolom_tersedia and c not in ['Kode Petugas',
                                                                                            col_id_cst]]]

            # D. LOGIKA FILTER WHITELIST (INTEGRASI GOOGLE SHEETS)
            if sheet_db is not None and not df_hasil.empty:
                data_whitelist = sheet_db.get_all_records()
                df_wl = pd.DataFrame(data_whitelist)
                if not df_wl.empty and 'ID Klien' in df_wl.columns and 'Rule' in df_wl.columns:
                    # Gabungkan ID dan Rule jadi satu kunci unik buat nyari kecocokan
                    df_hasil['Key_Cek'] = df_hasil['ID Klien'].astype(str) + "|" + df_hasil[
                        'Kategori Aturan (Rule)'].astype(str)
                    df_wl['Key_Cek'] = df_wl['ID Klien'].astype(str) + "|" + df_wl['Rule'].astype(str)

                    # Buang anomali yang ada di dalam database whitelist
                    df_hasil = df_hasil[~df_hasil['Key_Cek'].isin(df_wl['Key_Cek'])]
                    df_hasil.drop(columns=['Key_Cek'], inplace=True)

            os.remove(cst_path)
            os.remove(np_path)
            os.remove(petugas_path)

            st.session_state.df_hasil = df_hasil

        except Exception as e:
            st.error(f"FATAL ERROR: Terjadi kegagalan pada pipeline pemrosesan. Rincian: {e}")

# ==========================================
# 5. TATA LETAK MULTI-TAB (EXECUTIVE VIEW)
# ==========================================
# ==========================================
# 5. TATA LETAK MULTI-TAB (EXECUTIVE VIEW)
# ==========================================
if st.session_state.df_hasil is not None:
    df_hasil = st.session_state.df_hasil

    # 1. Deklarasi Tab SELALU DI LUAR pengecekan if-else agar selalu muncul
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Executive Summary", "📈 Analisis Visual Mendalam", "🗃️ Eksplorasi Data", "🛡️ Manajemen Whitelist"]
    )

    if df_hasil.empty:
        # Jika data bersih 100%, tampilkan pesan sukses di tab terkait
        with tab1:
            st.success(
                "🎉 Sempurna! Data valid dan tersinkronisasi 100%. Tidak ditemukan pelanggaran logika (atau semua anomali telah di-Whitelist).")
        with tab2:
            st.info("Tidak ada data anomali untuk dianalisis.")
        with tab3:
            st.info("Tabel eksplorasi kosong karena tidak ada anomali.")
    else:
        # Jika ada anomali, masukkan visualisasi dan tabel ke tab masing-masing

        # --- TAB 1: EXECUTIVE SUMMARY ---
        with tab1:
            st.subheader("🏆 Ringkasan Capaian Layanan")
            capaian = st.session_state.capaian_layanan

            cp1, cp2, cp3, cp4 = st.columns(4)
            cp1.metric(label="Dukungan Psikososial", value=f"{capaian['psiko']} Klien", help="Total ID Klien Unik")
            cp2.metric(label="On ART", value=f"{capaian['on_art']} Klien", help="Status 1, 2, dan 4")
            cp3.metric(label="LFU", value=f"{capaian['lfu']} Klien", help="Status 3")
            cp4.metric(label="Non-ART", value=f"{capaian['non_art']} Klien", help="Status 0")

            st.markdown("---")
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
                total_baris = st.session_state.total_baris_data
                skor_kesehatan = max(0, 100 - (total_anomali / total_baris * 100)) if total_baris > 0 else 0

                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=skor_kesehatan,
                    title={'text': "Kualitas Data (%)", 'font': {'size': 18}},
                    number={'suffix': "%", 'font': {'size': 42}},
                    gauge={
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                        'bgcolor': "rgba(0,0,0,0)",
                        'bar': {'color': "#00E676" if skor_kesehatan >= 90 else (
                            "#FFD600" if skor_kesehatan >= 75 else "#FF1744")},
                        'steps': [{'range': [0, 100], 'color': "rgba(128, 128, 128, 0.2)"}],
                        'threshold': {'line': {'color': "#FF1744", 'width': 4}, 'thickness': 0.75, 'value': 90}
                    }
                ))
                fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True, theme="streamlit")

            with col_chart2:
                st.write("**Komposisi Pelanggaran Data**")
                df_pie = df_hasil['Kategori Aturan (Rule)'].value_counts().reset_index()
                df_pie.columns = ['Rule', 'Jumlah']
                df_pie.loc[df_pie['Jumlah'] < (total_anomali * 0.05), 'Rule'] = 'Lainnya (<5%)'
                fig_pie = px.pie(df_pie, values='Jumlah', names='Rule', hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_traces(textposition='inside', textinfo='percent')
                fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20), showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True)

        # --- TAB 2: ANALISIS VISUAL ---
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
                    fig_wil = px.bar(df_wilayah.head(10), x='Jumlah', y='Wilayah', orientation='h', color='Jumlah',
                                     color_continuous_scale='Blues', text='Jumlah')
                    fig_wil.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400, showlegend=False)
                    fig_wil.update_traces(textposition='outside', textfont_size=13)
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
                    fig_petugas = px.bar(df_ptg_tampil, x='Jumlah', y='Nama Petugas', orientation='h', color='Jumlah',
                                         color_continuous_scale='Oranges', text='Jumlah')
                    fig_petugas.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400, showlegend=False)
                    fig_petugas.update_traces(textposition='outside', textfont_size=13)
                    st.plotly_chart(fig_petugas, use_container_width=True)
                else:
                    st.info("Data Petugas tidak tersedia.")

        # --- TAB 3: EKSPLORASI DATA & FORM JUSTIFY ---
        with tab3:
            st.subheader("Tabel Anomali & Pengecualian")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_hasil.to_excel(writer, index=False, sheet_name='Data Anomali')

            st.download_button(
                label="📥 Unduh Data Anomali (.xlsx)",
                data=output.getvalue(),
                file_name="Laporan_Anomali_DQA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

            st.dataframe(df_hasil, use_container_width=True, height=300)

            if sheet_db is not None:
                st.markdown("---")
                st.write("🛡️ **Form Pengecualian Data Khusus (Justify)**")
                st.caption("Gunakan form ini jika anomali di atas valid karena kondisi medis/lapangan khusus.")

                with st.form("form_justify"):
                    col_j1, col_j2 = st.columns(2)
                    with col_j1:
                        pilihan_id = st.selectbox("1. Pilih ID Klien yang Dikecualikan:",
                                                  df_hasil['ID Klien'].dropna().unique() if not df_hasil.empty else [
                                                      "-"])
                        pilihan_rule = st.selectbox("2. Aturan yang Dikecualikan:",
                                                    df_hasil[df_hasil['ID Klien'] == pilihan_id][
                                                        'Kategori Aturan (Rule)'].unique() if not df_hasil.empty and pilihan_id != "-" else [
                                                        "-"])
                    with col_j2:
                        alasan = st.text_input("3. Alasan Validitas Data (Wajib):")
                        petugas_monev = st.text_input("4. Nama Anda (Petugas Monev):")

                    submit_justify = st.form_submit_button("✅ Masukkan ke Whitelist", type="primary")

                    if submit_justify:
                        if alasan == "" or petugas_monev == "":
                            st.warning("Alasan dan Nama Petugas tidak boleh kosong!")
                        else:
                            try:
                                waktu = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                                lembaga_klien = df_hasil[df_hasil['ID Klien'] == pilihan_id]['Lembaga'].values[
                                    0] if 'Lembaga' in df_hasil.columns else "Tidak Diketahui"
                                sheet_db.append_row(
                                    [pilihan_id, pilihan_rule, alasan, petugas_monev, waktu, str(lembaga_klien)])
                                st.success(f"Berhasil! Data {pilihan_id} dari {lembaga_klien} telah dikecualikan.")
                            except Exception as e:
                                st.error(f"Gagal menghubungi server database: {e}")
            else:
                st.error("Sistem gagal terhubung ke Cloud Database. Fitur Whitelist dinonaktifkan.")

    # --- TAB 4: MANAJEMEN WHITELIST (ADMIN) - SEKARANG DI LUAR IF-ELSE ---
    with tab4:
        st.subheader("🛡️ Daftar Data Pengecualian (Whitelist)")
        if sheet_db is not None:
            data_wl = sheet_db.get_all_records()
            df_wl_tampil = pd.DataFrame(data_wl)

            if df_wl_tampil.empty:
                st.info("Belum ada data klien yang dimasukkan ke daftar pengecualian.")
            else:
                # Cek ketersediaan kolom 'Lembaga' di df_hasil
                # Karena df_hasil mungkin kosong (jika sukses 100%), gunakan session_state asli yg belum di-filter wl
                if 'df_hasil' in st.session_state and not st.session_state.df_hasil.empty and 'Lembaga' in st.session_state.df_hasil.columns:
                    lembaga_aktif = st.session_state.df_hasil['Lembaga'].dropna().unique().tolist()
                    if lembaga_aktif and 'Lembaga' in df_wl_tampil.columns:
                        df_wl_tampil = df_wl_tampil[df_wl_tampil['Lembaga'].isin(lembaga_aktif)]

                if df_wl_tampil.empty:
                    st.info(
                        "Aman. Tidak ada data pengecualian (whitelist) yang aktif untuk Lembaga pada file yang Anda unggah.")
                else:
                    st.dataframe(df_wl_tampil, use_container_width=True)

                    st.markdown("---")
                    st.write("❌ **Cabut Status Pengecualian (Unwhitelist) Khusus Lembaga Anda**")
                    with st.form("form_cabut"):
                        cabut_id = st.selectbox("Pilih ID Klien yang akan dihapus dari Whitelist:",
                                                df_wl_tampil['ID Klien'].unique())
                        submit_cabut = st.form_submit_button("Cabut Justify (Hapus)", type="primary")

                        if submit_cabut:
                            try:
                                cell = sheet_db.find(str(cabut_id))
                                if cell:
                                    sheet_db.delete_rows(cell.row)
                                    st.success(
                                        f"Pengecualian Klien {cabut_id} berhasil dicabut! Eksekusi ulang pipeline ETL untuk menyegarkan.")
                            except Exception as e:
                                st.error(f"Gagal mencabut data: {e}")