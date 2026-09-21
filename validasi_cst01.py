import pandas as pd
import threading
import io

# =========================================================================
# DATABASE INTERNAL: DATA INTERVENSI IU
# =========================================================================
DATABASE_INTERVENSI_IU = {
    "SPIRIT PARAMACITTA": ["Kab. Badung", "Kab. Buleleng", "Kota Denpasar", "Kab. Gianyar", "Kab. Tabanan",
                           "Kab. Jembrana"],
    "YAYASAN BATAMANG PLUS MANADO": ["Kota Manado", "Kota Bitung", "Kota Tomohon", "Kab. Gorontalo", "Kota Gorontalo",
                                     "Kota Ternate", "Kab. Halmahera Utara"],
    "YAYASAN CENDRAWASIH BERSATU PAPUA": ["Kab. Merauke", "Kab. Jayapura", "Kota Jayapura", "Kab. Jayawijaya",
                                          "Kab. Biak Numfor"],
    "YAYASAN CITA ANDARU BERSAMA": ["Kab. Tangerang", "Kab. Serang", "Kota Tangerang", "Kota Cilegon", "Kota Serang",
                                    "Kota Tangerang Selatan"],
    "YAYASAN FEMALE PLUS": ["Kab. Bogor", "Kab. Sukabumi", "Kab. Cianjur", "Kab. Bandung", "Kab. Garut",
                            "Kab. Tasikmalaya", "Kab. Ciamis", "Kab. Kuningan", "Kab. Cirebon", "Kab. Majalengka",
                            "Kab. Sumedang", "Kab. Indramayu", "Kab. Subang", "Kab. Purwakarta", "Kab. Karawang",
                            "Kab. Bekasi", "Kab. Bandung Barat", "Kota Bogor", "Kota Sukabumi", "Kota Bandung",
                            "Kota Cirebon", "Kota Bekasi", "Kota Depok", "Kota Cimahi", "Kota Tasikmalaya",
                            "Kab. Pangandaran"],
    "YAYASAN FLOBAMORA": ["Kota Palu", "Kab. Sikka", "Kota Kupang", "Kab. Belu"],
    "YAYASAN INSET - ODHA": ["Kab. Rejang Lebong", "Kota Bengkulu", "Kab. Lombok Barat", "Kab. Lombok Timur",
                             "Kota Mataram", "Kota Ambon", "Kab. Maluku Tenggara", "Kab. Sumbawa Barat"],
    "YAYASAN KANTI SEHATI SEJATI": ["Kota Bandar Lampung", "Kab. Lampung Timur", "Kab. Lampung Selatan",
                                    "Kab. Pringsewu", "Kota Jambi"],
    "YAYASAN KOMPAK": ["Kota Batam", "Kota Tanjung Pinang", "Kab. Karimun"],
    "YAYASAN KP MAHAKAM PLUS": ["Kab. Kutai Kartanegara", "Kab. Kutai Timur", "Kota Balikpapan", "Kota Samarinda",
                                "Kota Tarakan", "Kota Bontang"],
    "YAYASAN MAHAMERU": ["Kab. Tulungagung", "Kab. Blitar", "Kab. Kediri", "Kab. Malang", "Kab. Jember",
                         "Kab. Banyuwangi", "Kab. Situbondo", "Kab. Probolinggo", "Kab. Pasuruan", "Kab. Sidoarjo",
                         "Kab. Mojokerto", "Kab. Jombang", "Kab. Nganjuk", "Kab. Madiun", "Kab. Gresik", "Kota Kediri",
                         "Kota Blitar", "Kota Malang", "Kota Pasuruan", "Kota Madiun", "Kota Surabaya",
                         "Kab. Trenggalek", "Kab. Bojonegoro", "Kab. Lumajang", "Kab. Lamongan", "Kota Mojokerto",
                         "Kab. Tuban", "Kab. Ngawi", "Kab. Ponorogo"],
    "YAYASAN MEDAN PLUS": ["Kota Banda Aceh", "Kota Lhokseumawe", "Kab. Labuhan Batu", "Kab. Asahan", "Kab. Simalungun",
                           "Kab. Deli Serdang", "Kota Pematang Siantar", "Kota Tebing Tinggi", "Kota Medan",
                           "Kab. Karo", "Kota Padangsidimpuan", "Kab. Toba Samosir"],
    "YAYASAN PELITA ILMU (IU)": ["Kota Jakarta Selatan", "Kota Jakarta Timur", "Kota Jakarta Pusat",
                                 "Kota Jakarta Barat", "Kota Jakarta Utara"],
    "YAYASAN PONTIANAK PLUS - ODHA": ["Kab. Mempawah", "Kab. Ketapang", "Kota Pontianak", "Kota Singkawang",
                                      "Kab. Kotawaringin Timur", "Kota Palangka Raya", "Kab. Banjar",
                                      "Kota Banjarmasin", "Kab. Tanah Bumbu", "Kab. Sintang", "Kab. Sambas"],
    "YAYASAN SEBAYA LANCANG KUNING": ["Kota Padang", "Kota Solok", "Kota Bukittinggi", "Kab. Indragiri Hilir",
                                      "Kota Pekanbaru", "Kota Dumai"],
    "YAYASAN SEHAT PEDULI KASIH": ["Kab. Cilacap", "Kab. Banyumas", "Kab. Purbalingga", "Kab. Banjarnegara",
                                   "Kab. Kebumen", "Kab. Wonosobo", "Kab. Magelang", "Kab. Boyolali", "Kab. Sukoharjo",
                                   "Kab. Wonogiri", "Kab. Karanganyar", "Kab. Sragen", "Kab. Grobogan", "Kab. Pati",
                                   "Kab. Kudus", "Kab. Jepara", "Kab. Demak", "Kab. Semarang", "Kab. Temanggung",
                                   "Kab. Kendal", "Kab. Batang", "Kab. Pemalang", "Kab. Tegal", "Kab. Brebes",
                                   "Kota Magelang", "Kota Surakarta", "Kota Salatiga", "Kota Semarang",
                                   "Kota Pekalongan", "Kota Tegal", "Kab. Pekalongan", "Kab. Klaten", "Kab. Blora",
                                   "Kab. Rembang"],
    "YAYASAN SORONG SEHATI": ["Kab. Nabire", "Kab. Mimika", "Kab. Paniai", "Kab. Manokwari", "Kota Sorong",
                              "Kab. Fakfak", "Kab. Sorong"],
    "YAYASAN SRIWIJAYA PLUS": ["Kota Pangkal Pinang", "Kab. Bangka", "Kab. Banyuasin", "Kota Palembang",
                               "Kota Prabumulih", "Kab. Musi Banyuasin"],
    "YAYASAN VICTORY PLUS YOGYAKARTA": ["Kab. Bantul", "Kab. Sleman", "Kota Yogyakarta", "Kab. Gunung Kidul"],
    "YPKDS SULAWESI SELATAN": ["Kab. Jeneponto", "Kab. Gowa", "Kab. Sidenreng Rappang", "Kota Makassar",
                               "Kota Parepare", "Kota Palopo", "Kota Kendari", "Kota Baubau", "Kab. Mamuju",
                               "Kab. Bulukumba"]
}


def bersihkan_nama_wilayah(teks):
    if not teks or pd.isna(teks): return ""
    t = str(teks).upper()
    for hapus in ["KAB.", "KABUPATEN", "KOTA", "ADM.", "ADM"]:
        t = t.replace(hapus, "")
    return "".join(t.split())


def bersihkan_nama_iu(teks):
    if not teks or pd.isna(teks): return ""
    return "".join(str(teks).upper().split())


DATABASE_IU_BERSIH = {}
# Mempersiapkan database IU untuk Rule 23
for nama_iu_asli, daftar_wilayah in DATABASE_INTERVENSI_IU.items():
    key_iu_bersih = bersihkan_nama_iu(nama_iu_asli)
    wilayah_bersih = [bersihkan_nama_wilayah(w) for w in daftar_wilayah]
    DATABASE_IU_BERSIH[key_iu_bersih] = (nama_iu_asli, wilayah_bersih)


# =========================================================================
# FUNGSI PEMBACA UNIVERSAL ULTIMATE (Mode Tahan Banting)
# =========================================================================
def baca_file_otomatis(file_path):
    # 1. Coba baca sebagai Excel murni (.xlsx, .xls, .xlsb)
    try:
        df = pd.read_excel(file_path, header=0, dtype=str)
        if not df.empty:
            return df
    except Exception:
        pass

    # BACA PAKSA SEBAGAI TEKS MENTAH (Ganti karakter siluman jadi '?')
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        # Decode paksa, error di-replace biar gak crash
        isi_teks_aman = raw_data.decode('utf-8', errors='replace')
    except Exception as e:
        raise ValueError(f"Gagal membaca fisik file. Error: {e}")

    # 2. Coba baca sebagai HTML yang nyamar jadi Excel
    try:
        tabel_html = pd.read_html(io.StringIO(isi_teks_aman), header=0)
        if len(tabel_html) > 0:
            return tabel_html[0].astype(str)
    except Exception:
        pass

    # 3. Coba baca sebagai file teks TSV
    try:
        df = pd.read_csv(io.StringIO(isi_teks_aman), header=0, dtype=str, sep='\t', low_memory=False, quoting=3,
                         on_bad_lines='skip')
        if len(df.columns) > 1:
            return df
    except Exception:
        pass

    # 4. Fallback terakhir: Baca sebagai CSV biasa
    try:
        df = pd.read_csv(io.StringIO(isi_teks_aman), header=0, dtype=str, sep=',', low_memory=False, quoting=3,
                         on_bad_lines='skip')
        return df
    except Exception as e:
        raise ValueError(f"Sistem menyerah. File ini formatnya benar-benar hancur. Error: {e}")


# =========================================================================
# FUNGSI UTAMA: VALIDASI 27 RULE
# =========================================================================
def bersihkan_dan_validasi_laporan(file_cst_path, file_np_path, update_status=None):
    # Fungsi kecil untuk melapor status ke GUI
    def lapor(pesan):
        if update_status: update_status(pesan)

    lapor("Membaca data file CST-01...")
    # Proses baca file
    df_cst = baca_file_otomatis(file_cst_path)
    if not df_cst.empty and 'Tanggal' in df_cst.columns and not df_cst['Tanggal'].empty:
        if str(df_cst['Tanggal'].iloc[0]).strip() == 'dd/mm/yyyy':
            df_cst = df_cst.drop(0).reset_index(drop=True)

    lapor("Membaca data file NP-03...")
    df_np = baca_file_otomatis(file_np_path)
    df_cst.columns = df_cst.columns.str.strip().str.replace('\n', ' ')
    df_np.columns = df_np.columns.str.strip().str.replace('\n', ' ')

    lapor("Menyelaraskan format dan nama kolom...")
    # Pencarian Kolom Dinamis (menyesuaikan berbagai versi penamaan kolom)
    kolom_tgl_input_cst = 'Tanggal Input'
    for col in df_cst.columns:
        if col.lower() in ['tanggal input', 'tgl input', 'waktu input', 'created at']: kolom_tgl_input_cst = col

    kolom_tgl_np_terdeteksi = 'Tanggal Tes HIV'
    kolom_prep = 'PrEP Terima Obat'

    for col in df_np.columns:
        # 1. Hapus semua spasi dan enter agar teks menjadi gabung semua
        col_bersih = "".join(str(col).lower().split())

        # 2. Cek kecocokan menggunakan col_bersih, perhatikan teksnya digabung semua
        if col_bersih in ['tanggalteshiv', 'tanggaltes', 'tanggal', 'tgl', 'tgltes', 'tanggaldd/mm/yyyy']:
            kolom_tgl_np_terdeteksi = col

        if 'prep' in col_bersih and ('terima' in col_bersih or 'obat' in col_bersih or 'beri' in col_bersih):
            kolom_prep = col
        elif 'prep' in col_bersih and kolom_prep == 'PrEP Terima Obat':
            kolom_prep = col

    kolom_iu_cst, kolom_kab_cst = 'IU', 'Kabupaten/Kota'
    for col in df_cst.columns:
        if col.lower() in ['iu', 'implementing unit', 'nama iu', 'lembaga']: kolom_iu_cst = col
        if col.lower() in ['kabupaten/kota', 'kabkota', 'kabupaten', 'kota', 'wilayah', 'nama kota']: kolom_kab_cst = col

    kolom_iu_np, kolom_kab_np = 'IU', 'Kabupaten/Kota'
    for col in df_np.columns:
        if col.lower() in ['iu', 'implementing unit', 'nama iu', 'lembaga']: kolom_iu_np = col
        if col.lower() in ['kabupaten/kota', 'kabkota', 'kabupaten', 'kota', 'wilayah', 'nama kota']: kolom_kab_np = col

    kolom = {
        'id_klien': 'ID Klien', 'nik': 'NIK', 'umur': 'Umur', 'tipe_klien': 'Tipe Klien',
        'tanggal': 'Tanggal', 'tgl_tahu_status': 'Tahun Status HIV', 'tgl_input': kolom_tgl_input_cst,
        'art': 'Status Pengobatan [data : d]', 'lfu': 'Status LFU ARV', 'layanan_art': 'Layanan on ART',
        'jenis_kegiatan': 'Jenis Kegiatan', 'lokasi': 'Lokasi', 'rujukan_keluar': 'Rujukan Keluar',
        'iu': kolom_iu_cst, 'kabupaten': kolom_kab_cst
    }

    kolom_np = {
        'id_klien': 'ID Klien', 'nik': 'NIK',
        'hasil_tes': 'Hasil Tes HIV', 'menerima_vct': 'Menerima Hasil VCT', 'prep': kolom_prep,
        'tgl_tes': kolom_tgl_np_terdeteksi, 'iu': kolom_iu_np, 'kabupaten': kolom_kab_np
    }

    # Konversi format tanggal agar seragam
    if not df_np.empty and kolom_np['tgl_tes'] in df_np.columns and not df_np[kolom_np['tgl_tes']].empty:
        if str(df_np[kolom_np['tgl_tes']].iloc[0]).strip() == 'dd/mm/yyyy':
            df_np = df_np.drop(0).reset_index(drop=True)

    if kolom['tanggal'] in df_cst.columns:
        df_cst[kolom['tanggal']] = pd.to_datetime(df_cst[kolom['tanggal']], errors='coerce')
    if kolom['tgl_tahu_status'] in df_cst.columns:
        df_cst[kolom['tgl_tahu_status']] = pd.to_datetime(df_cst[kolom['tgl_tahu_status']], errors='coerce')
    if kolom['tgl_input'] in df_cst.columns:
        df_cst[kolom['tgl_input']] = pd.to_datetime(df_cst[kolom['tgl_input']], errors='coerce')
    if kolom_np['tgl_tes'] in df_np.columns:
        df_np[kolom_np['tgl_tes']] = pd.to_datetime(df_np[kolom_np['tgl_tes']], errors='coerce')

    if kolom['id_klien'] in df_cst.columns and kolom['tanggal'] in df_cst.columns:
        df_cst = df_cst.sort_values(by=[kolom['id_klien'], kolom['tanggal']], ascending=[True, True]).reset_index(
            drop=True)

    # Dictionary Kumpulan Error untuk output TXT
    kumpulan_error = {
        "Rule 1: ID Klien Standar": [], "Rule 2: NIK Wajib Valid": [], "Rule 3: Anti NIK Silang": [],
        "Rule 4: Batasan Umur Anak": [], "Rule 5: Tanggal Input Valid": [], "Rule 6: Wajib Tipe Anak": [],
        "Rule 7: Mesin Waktu": [], "Rule 8: Layanan ART Tidak Boleh Kosong": [], "Rule 9: Sinkronisasi VO": [],
        "Rule 10: Inisiasi ART Wajib Jenis Kegiatan 2": [], "Rule 11: Status ART/LFU di Tanggal Tahu Status": [],
        "Rule 12: Inisiasi ART Wajib Rujukan Keluar 5/6": [], "Rule 13: Pantang Mundur ke ART 0": [],
        "Rule 14: Syarat Putus Obat (LFU 1)": [], "Rule 15: Validasi Riwayat LFU 2": [],
        "Rule 16: Filter Pertama LFU 2 Anti ART 2": [], "Rule 17: Syarat Wajib VCT": [],
        "Rule 18: Larangan Isi Tes HIV": [], "Rule 19: Sinkronisasi Klien Reaktif": [],
        "Rule 20: Kontak Perdana Wajib Sinkron": [], "Rule 21: Status Pengobatan Awal": [],
        "Rule 22: Smart Detection & Anti-Crash": [], "Rule 23: Kesesuaian Wilayah Intervensi IU": [],
        "Rule 24: Reaktif Anti PrEP": [], "Rule 25: Non-Reaktif & N/A Anti CST": [],
        "Rule 24: Reaktif Anti PrEP": [], "Rule 25: Non-Reaktif & N/A Anti CST": [],
        "Rule 26: Inisiasi ART Ganda": [], "Rule 27: Rentang LFU Back ART": []
    }
    seen_errors = set()

    def catat_error(rule_name, id_kl, tgl, alasan, per_tanggal=False):
        error_key = (rule_name, id_kl, tgl, alasan) if per_tanggal else (rule_name, id_kl, alasan)
        if error_key not in seen_errors:
            seen_errors.add(error_key)
            tgl_str = tgl.strftime('%Y-%m-%d') if pd.notna(tgl) and isinstance(tgl, pd.Timestamp) else "General"
            pesan = f"-> Peringatan Sistem: {alasan}" if id_kl == "ALL" else f"-> Klien {id_kl} (Laporan: {tgl_str}) : {alasan}"
            kumpulan_error[rule_name].append(pesan)

    # RULE 22: Deteksi kolom krusial (Anti-Crash)
    if kolom_np['tgl_tes'] not in df_np.columns:
        catat_error("Rule 22: Smart Detection & Anti-Crash", "ALL", pd.NaT,
                    f"Kolom Tanggal tidak terdeteksi di file NP-03 (Dicari: {kolom_np['tgl_tes']})")

    id_to_niks, nik_to_ids, semua_id_cst, id_to_nik_cst, nik_to_id_cst = {}, {}, set(), {}, {}

    list_cst = df_cst.to_dict('records')
    # Pre-processing Map NIK & ID
    for row in list_cst:
        id_k = str(row.get(kolom['id_klien'], '')).strip()
        if id_k.lower() in ['nan', '']: continue
        semua_id_cst.add(id_k)

        n_raw = str(row.get(kolom['nik'], '')).replace("'", "").strip()
        if n_raw.endswith('.0'): n_raw = n_raw[:-2]

        if id_k not in id_to_nik_cst or id_to_nik_cst[id_k].lower() in ['nan', '', 'xx', 'nat']: id_to_nik_cst[
            id_k] = n_raw
        if n_raw.lower() not in ['nan', '', 'xx', 'nat'] and n_raw not in nik_to_id_cst: nik_to_id_cst[n_raw] = id_k

        if n_raw.lower() not in ['nan', '', 'xx', 'nat']:
            if id_k not in id_to_niks: id_to_niks[id_k] = set()
            id_to_niks[id_k].add(n_raw)
            if n_raw not in nik_to_ids: nik_to_ids[n_raw] = set()
            nik_to_ids[n_raw].add(id_k)

    lapor("Memeriksa Rule 1 - 12 & 23 (Validasi Dasar CST-01)...")
    # RULE 3: Pengecekan NIK Silang / Ganda (Satu ID banyak NIK atau Satu NIK banyak ID)
    for id_k, niks in id_to_niks.items():
        if len(niks) > 1: catat_error("Rule 3: Anti NIK Silang", id_k, pd.NaT,
                                      f"Memiliki lebih dari 1 NIK yang berbeda ({', '.join(niks)})")
    for n_raw, ids in nik_to_ids.items():
        if len(ids) > 1:
            ids_lain = [i for i in ids if i != list(ids)[0]]
            catat_error("Rule 3: Anti NIK Silang", list(ids)[0], pd.NaT,
                        f"NIK '{n_raw}' terindikasi ganda, dipakai juga oleh: {', '.join(ids_lain)}")

    # ========================== VALIDASI DATA CST-01 ==========================
    for row in list_cst:
        id_klien = str(row.get(kolom['id_klien'], '')).strip()
        tgl_kontak = row.get(kolom['tanggal'], pd.NaT)
        tgl_input = row.get(kolom['tgl_input'], pd.NaT)
        if id_klien.lower() in ['nan', '']: continue

        # RULE 1: ID Klien Standar (Harus 10, 12 digit, atau 11 berakhiran A/B)
        panjang_id = len(id_klien)
        if panjang_id == 11:
            if id_klien[-1].upper() not in ['A', 'B']:
                catat_error("Rule 1: ID Klien Standar", id_klien, tgl_kontak,
                            f"Panjang 11 digit tapi berakhiran '{id_klien[-1]}' (wajib berakhiran A atau B)")
        elif panjang_id not in [10, 12]:
            catat_error("Rule 1: ID Klien Standar", id_klien, tgl_kontak,
                        f"Panjang tidak standar ({panjang_id} digit, wajib berukuran 10, 12, atau 11 dengan akhiran A/B)")

        # RULE 2: Validasi Format NIK (16 Digit, Bukan Dummy)
        nik_raw = str(row.get(kolom['nik'], '')).replace("'", "").strip()
        nik = nik_raw[:-2] if nik_raw.endswith('.0') else nik_raw
        if nik.lower() not in ['nan', '', 'xx', 'nat']:
            if len(nik) != 16:
                catat_error("Rule 2: NIK Wajib Valid", id_klien, tgl_kontak, f"Tidak 16 digit (terbaca: '{nik}')")
            elif nik.endswith('000'):
                catat_error("Rule 2: NIK Wajib Valid", id_klien, tgl_kontak, f"Berakhiran angka 000 (terbaca: '{nik}')")

        umur = pd.to_numeric(row.get(kolom['umur']), errors='coerce')
        tipe = str(row.get(kolom['tipe_klien'], '')).replace(".0", "").strip()

        # RULE 4: Batasan Umur Anak (Umur >= 18 nggak boleh Tipe Anak)
        if tipe == '9100' and pd.notna(umur) and umur >= 18:
            catat_error("Rule 4: Batasan Umur Anak", id_klien, tgl_kontak,
                        f"Tipe Klien Anak (9100) tapi umur {int(umur)} thn")

        # RULE 5: Tgl Input Sistem nggak boleh mendahului Tgl Kontak
        if pd.notna(tgl_kontak) and pd.notna(tgl_input):
            if tgl_input.normalize() < tgl_kontak.normalize():
                catat_error("Rule 5: Tanggal Input Valid", id_klien, tgl_kontak,
                            f"Tanggal Input sistem ({tgl_input.strftime('%Y-%m-%d')}) tercatat lebih dulu daripada Tanggal Kontak")

        # RULE 6: Wajib Tipe Anak (Umur < 18 wajib Tipe 9100)
        if pd.notna(umur) and umur < 18 and tipe not in ['9100', 'nan', '']:
            catat_error("Rule 6: Wajib Tipe Anak", id_klien, tgl_kontak,
                        f"Umur {int(umur)} thn (<18) tapi Tipe Klien {tipe}")

        tgl_status = row.get(kolom['tgl_tahu_status'], pd.NaT)
        art = pd.to_numeric(row.get(kolom['art']), errors='coerce')
        lfu = pd.to_numeric(row.get(kolom['lfu']), errors='coerce')

        # RULE 7: Mesin Waktu (Tanggal Kontak nggak boleh sebelum Tgl Tahu Status HIV)
        if pd.notna(tgl_kontak) and pd.notna(tgl_status) and tgl_kontak < tgl_status:
            catat_error("Rule 7: Mesin Waktu", id_klien, tgl_kontak,
                        "Tanggal kontak mendahului Tanggal Tahu Status HIV")

        # RULE 8: Layanan on ART wajib diisi jika statusnya ART
        layanan = str(row.get(kolom['layanan_art'], '')).strip()
        if art in [0, 1, 2, 3, 4] and layanan.lower() in ['', 'nan']:
            catat_error("Rule 8: Layanan ART Tidak Boleh Kosong", id_klien, tgl_kontak,
                        f"Status ART {int(art)} tapi 'Layanan on ART' kosong")

        # RULE 9: Sinkronisasi VO (Jenis Kegiatan 4 harus di Lokasi VO, dan sebaliknya)
        if kolom['jenis_kegiatan'] in df_cst.columns and kolom['lokasi'] in df_cst.columns:
            jenis = str(row.get(kolom['jenis_kegiatan'], '')).replace('.0', '').strip()
            lokasi = str(row.get(kolom['lokasi'], '')).strip().upper()
            if jenis == '4' and 'VO' not in lokasi:
                catat_error("Rule 9: Sinkronisasi VO", id_klien, tgl_kontak,
                            f"Jenis Kegiatan {jenis} tapi Lokasi bukan VO ('{lokasi}')", per_tanggal=True)
            elif 'VO' in lokasi and jenis != '4':
                catat_error("Rule 9: Sinkronisasi VO", id_klien, tgl_kontak,
                            f"Lokasi 'VO' tapi Jenis Kegiatan bukan 4 ('{jenis}')", per_tanggal=True)

        # RULE 10: Inisiasi ART (ART 1) wajib memiliki Jenis Kegiatan = 2
        jenis_keg_raw = str(row.get(kolom['jenis_kegiatan'], '')).replace('.0', '').strip()
        if art == 1 and jenis_keg_raw != '2':
            catat_error("Rule 10: Inisiasi ART Wajib Jenis Kegiatan 2", id_klien, tgl_kontak,
                        f"Status ART 1 tetapi Jenis Kegiatan bukan 2 (terbaca: '{jenis_keg_raw}')")

        # RULE 11: Pada Tgl Tahu Status, wajib berstatus ART 0 atau ART 1 (Inisiasi)
        if pd.notna(tgl_kontak) and pd.notna(tgl_status) and tgl_kontak == tgl_status:
            if not ((art == 0 and lfu == 0) or (art == 1 and lfu == 0)):
                art_str = int(art) if pd.notna(art) else 'Kosong'
                lfu_str = int(lfu) if pd.notna(lfu) else 'Kosong'
                catat_error("Rule 11: Status ART/LFU di Tanggal Tahu Status", id_klien, tgl_kontak,
                            f"Tgl Kontak = Tgl Tahu Status, wajib ART 0/1 dan LFU 0 (Terbaca: ART {art_str} LFU {lfu_str})")

        # RULE 12: Inisiasi ART wajib Rujukan Keluar 5 atau 6
        if art == 1:
            rujukan_val = str(row.get(kolom['rujukan_keluar'], '')).replace('.0', '').strip()
            if '5' not in rujukan_val and '6' not in rujukan_val:
                catat_error("Rule 12: Inisiasi ART Wajib Rujukan Keluar 5/6", id_klien, tgl_kontak,
                            f"Inisiasi ART (ART 1) tetapi Rujukan Keluar tidak memuat opsi 5 atau 6 (Terbaca: '{rujukan_val}')")

        # RULE 23: Cek kesesuaian wilayah intervensi lembaga (IU)
        if kolom['iu'] in df_cst.columns and kolom['kabupaten'] in df_cst.columns:
            iu_cst = str(row.get(kolom['iu'], '')).strip()
            kab_cst = str(row.get(kolom['kabupaten'], '')).strip()
            iu_cst_bersih = bersihkan_nama_iu(iu_cst)
            kab_cst_bersih = bersihkan_nama_wilayah(kab_cst)
            if iu_cst_bersih in DATABASE_IU_BERSIH:
                nama_iu_resmi, wilayah_sah = DATABASE_IU_BERSIH[iu_cst_bersih]
                if kab_cst_bersih not in ['NAN', ''] and kab_cst_bersih not in wilayah_sah:
                    catat_error("Rule 23: Kesesuaian Wilayah Intervensi IU", id_klien, tgl_kontak,
                                f"[CST-01] Lembaga '{iu_cst}' terdeteksi di '{kab_cst}' (di luar wilayah resmi).")

    lapor("Cek Riwayat Pengobatan & LFU (Rule 13 - 16, 26, 27)...")
    # VALIDASI RIWAYAT (Berdasarkan urutan kontak)
    cst_tgl_dukungan, cst_art_pertama = {}, {}
    if kolom['id_klien'] in df_cst.columns:
        for id_k, group in df_cst.groupby(kolom['id_klien']):
            if str(id_k).lower() in ['nan', '']: continue
            prev_art, prev_lfu, prev_smt = None, None, None
            tgl_art_aktif_terakhir = pd.NaT
            smt_berjalan_lfu2 = None
            has_art1_lfu0 = False
            last_art1_lfu2_date = pd.NaT

            tgls = group[kolom['tanggal']].dropna()
            cst_tgl_dukungan[id_k] = set(tgls.dt.strftime('%Y-%m-%d'))
            if not group.empty: cst_art_pertama[id_k] = str(group.iloc[0].get(kolom['art'], '')).replace('.0',
                                                                                                         '').strip()

            list_group = group.to_dict('records')
            for row in list_group:
                art = pd.to_numeric(row.get(kolom['art']), errors='coerce')
                lfu = pd.to_numeric(row.get(kolom['lfu']), errors='coerce')
                tgl_kontak = row.get(kolom['tanggal'], pd.NaT)
                if pd.isna(art) or pd.isna(lfu) or pd.isna(tgl_kontak): continue

                smt_sekarang = f"{tgl_kontak.year}-S{1 if tgl_kontak.month <= 6 else 2}"
                if pd.notna(prev_smt) and smt_sekarang != prev_smt: smt_berjalan_lfu2 = None

                # RULE 26: ART 1 LFU 0 cuma boleh terjadi satu kali seumur hidup klien
                if art == 1 and lfu == 0:
                    if has_art1_lfu0:
                        catat_error("Rule 26: Inisiasi ART Ganda", id_k, tgl_kontak,
                                    "Ditemukan riwayat ART 1 LFU 0 lebih dari satu kali")
                    has_art1_lfu0 = True

                # RULE 27: Kembali inisiasi (ART 1 LFU 2) harus > 60 hari sejak LFU 2 terakhir
                if art == 1 and lfu == 2:
                    if pd.notna(last_art1_lfu2_date):
                        selisih_lfu2 = (tgl_kontak - last_art1_lfu2_date).days
                        if selisih_lfu2 <= 60:
                            catat_error("Rule 27: Rentang LFU Back ART", id_k, tgl_kontak,
                                        f"Jarak Inisiasi kembali (ART 1 LFU 2) hanya {selisih_lfu2} hari (Wajib > 60 hari)")
                    last_art1_lfu2_date = tgl_kontak

                # RULE 13: Kalau sudah pernah pengobatan (ART > 0), tidak boleh mundur jadi Belum ART (ART 0)
                if prev_art in [1, 2, 3, 4] and art == 0:
                    catat_error("Rule 13: Pantang Mundur ke ART 0", id_k, tgl_kontak,
                                f"ART 0 padahal sebelumnya sudah ART {int(prev_art)}")

                # RULE 14: Dicatat Putus Obat (LFU 1) syaratnya sudah absen > 60 hari dari kontak aktif terakhir
                if art == 3 and lfu == 1 and pd.notna(tgl_art_aktif_terakhir):
                    selisih_hari = (tgl_kontak - tgl_art_aktif_terakhir).days
                    if selisih_hari <= 60:
                        catat_error("Rule 14: Syarat Putus Obat (LFU 1)", id_k, tgl_kontak,
                                    f"Baru {selisih_hari} hari sejak kontak aktif terakhir (ART 1/2), wajib >60 hari")

                # RULE 15 & 16: Validasi kelogisan transisi status LFU 2 (Kembali Pengobatan setelah putus)
                if lfu == 2:
                    if prev_lfu != 2:
                        if not (prev_art == 3 and prev_lfu == 1): catat_error("Rule 15: Validasi Riwayat LFU 2", id_k,
                                                                              tgl_kontak,
                                                                              f"Pelanggaran: LFU 2 wajib didahului ART 3 LFU 1. Terbaca: ART {prev_art} LFU {prev_lfu}")
                        if art == 2: catat_error("Rule 16: Filter Pertama LFU 2 Anti ART 2", id_k, tgl_kontak,
                                                 "Kontak pertama LFU 2 langsung berstatus ART 2 (Wajib diawali ART 1)")
                    else:
                        if art not in [1, 2, 4]: catat_error("Rule 15: Validasi Riwayat LFU 2", id_k, tgl_kontak,
                                                             f"Kombinasi tidak sah: ART {int(art)} tidak boleh dengan LFU 2")
                    smt_berjalan_lfu2 = smt_sekarang

                if smt_berjalan_lfu2 == smt_sekarang and prev_lfu == 2 and lfu == 0:
                    catat_error("Rule 15: Validasi Riwayat LFU 2", id_k, tgl_kontak,
                                "Kembali LFU 0 padahal sudah terlanjur LFU 2 di semester ini")

                prev_art, prev_lfu, prev_smt = art, lfu, smt_sekarang
                if art in [1, 2] and lfu == 0: tgl_art_aktif_terakhir = tgl_kontak

    lapor("Memeriksa Rule 17 - 25 (Validasi Tes HIV & Sinkronisasi NP-03)...")
    # ========================== VALIDASI DATA NP-03 ==========================
    list_np = df_np.to_dict('records')
    for row in list_np:
        id_np = str(row.get(kolom_np['id_klien'], '')).strip()
        nik_raw_np = str(row.get(kolom_np['nik'], '')).replace("'", "").strip()
        nik_np = nik_raw_np[:-2] if nik_raw_np.endswith('.0') else nik_raw_np

        hasil_tes = str(row.get(kolom_np['hasil_tes'], '')).replace('.0', '').strip()
        terima_vct = str(row.get(kolom_np['menerima_vct'], '')).replace('.0', '').strip()
        tgl_tes = row.get(kolom_np['tgl_tes'], pd.NaT)
        prep_status = str(row.get(kolom_np['prep'], '')).replace('.0', '').strip().lower()
        if id_np.lower() in ['nan', '']: continue

        id_ada_di_cst = id_np in semua_id_cst
        nik_cst_dari_id = id_to_nik_cst.get(id_np, '')
        is_nik_np_kosong = nik_np.lower() in ['nan', '', 'xx', 'nat']
        is_nik_cst_kosong = nik_cst_dari_id.lower() in ['nan', '', 'xx', 'nat']

        # RULE 17: Kalau ada hasil tes HIV, status Menerima VCT harus '1' (Ya)
        if hasil_tes not in ['3', '0', 'nan', ''] and terima_vct != '1':
            catat_error("Rule 17: Syarat Wajib VCT", id_np, tgl_tes,
                        "Ada Hasil Tes HIV, tetapi status Menerima Hasil VCT BUKAN 1")

        # RULE 18: Kalau Menerima VCT bukan '1', maka nggak boleh ada Hasil Tes HIV
        if terima_vct != '1' and hasil_tes not in ['3', '0', 'nan', '']:
            catat_error("Rule 18: Larangan Isi Tes HIV", id_np, tgl_tes,
                        "Tidak Menerima VCT, tetapi Hasil Tes HIV malah terisi")

        is_reaktif = (hasil_tes == '1')

        # RULE 24: Pasien Reaktif tidak boleh menerima PrEP (Profilaksis Pra-Pajanan)
        if is_reaktif and prep_status in ['1', 'ya', 'yes', 'y']:
            catat_error("Rule 24: Reaktif Anti PrEP", id_np, tgl_tes,
                        "Hasil Tes HIV Reaktif (1) tetapi tercatat Menerima Obat PrEP")

        # RULE 25: Pasien Non-Reaktif / Belum Tes nggak boleh ada di data CST-01 (Pengobatan)
        if hasil_tes in ['2', '0', '3', 'nan', ''] and id_ada_di_cst:
            catat_error("Rule 25: Non-Reaktif & N/A Anti CST", id_np, tgl_tes,
                        "Hasil tes Non-Reaktif atau N/A tetapi ID Klien ditemukan di data pengobatan CST-01")

        # RULE 19, 20, 21: Sinkronisasi Reaktif -> Wajib masuk CST, NIK harus sama, Tgl Sinkron
        if is_reaktif:
            if not id_ada_di_cst:
                if not is_nik_np_kosong and nik_np in nik_to_id_cst:
                    catat_error("Rule 19: Sinkronisasi Klien Reaktif", id_np, tgl_tes,
                                f"ID tidak terdaftar di CST-01, tetapi NIK cocok dengan Klien {nik_to_id_cst[nik_np]}")
                else:
                    catat_error("Rule 19: Sinkronisasi Klien Reaktif", id_np, tgl_tes,
                                "Reaktif tapi belum didaftarkan di CST-01")
            else:
                if is_nik_np_kosong and is_nik_cst_kosong:
                    pass
                elif is_nik_np_kosong and not is_nik_cst_kosong:
                    catat_error("Rule 19: Sinkronisasi Klien Reaktif", id_np, tgl_tes,
                                f"NIK di NP-03 kosong, padahal di file CST-01 terisi ({nik_cst_dari_id})")
                elif not is_nik_np_kosong and is_nik_cst_kosong:
                    catat_error("Rule 19: Sinkronisasi Klien Reaktif", id_np, tgl_tes,
                                f"NIK di NP-03 terisi ({nik_np}), tetapi di file CST-01 masih kosong")
                elif nik_np != nik_cst_dari_id:
                    catat_error("Rule 19: Sinkronisasi Klien Reaktif", id_np, tgl_tes,
                                f"NIK NP-03 ({nik_np}) berbeda dengan NIK di CST-01 ({nik_cst_dari_id})")

            # RULE 20: Tgl Tes NP-03 harus tercatat sebagai Tgl Kontak di CST-01
            if id_ada_di_cst and pd.notna(tgl_tes) and isinstance(tgl_tes, pd.Timestamp):
                if tgl_tes.strftime('%Y-%m-%d') not in cst_tgl_dukungan.get(id_np, set()):
                    catat_error("Rule 20: Kontak Perdana Wajib Sinkron", id_np, tgl_tes,
                                "Tidak ada laporan di CST-01 pada tanggal ini")

            # RULE 21: Awal masuk CST harus mulai dari ART 0 (Belum) atau ART 1 (Inisiasi)
            if id_ada_di_cst and cst_art_pertama.get(id_np) not in ['0', '1']:
                catat_error("Rule 21: Status Pengobatan Awal", id_np, tgl_tes,
                            f"Awal kontak di CST-01 berstatus ART {cst_art_pertama.get(id_np)} (Harus 0 atau 1)")

        if kolom_np['iu'] in df_np.columns and kolom_np['kabupaten'] in df_np.columns:
            iu_np = str(row.get(kolom_np['iu'], '')).strip()
            kab_np = str(row.get(kolom_np['kabupaten'], '')).strip()
            iu_np_bersih = bersihkan_nama_iu(iu_np)
            kab_np_bersih = bersihkan_nama_wilayah(kab_np)
            if iu_np_bersih in DATABASE_IU_BERSIH:
                nama_iu_resmi, wilayah_sah = DATABASE_IU_BERSIH[iu_np_bersih]
                if kab_np_bersih not in ['NAN', ''] and kab_np_bersih not in wilayah_sah:
                    catat_error("Rule 23: Kesesuaian Wilayah Intervensi IU", id_np, tgl_tes,
                                f"[NP-03] Lembaga '{iu_np}' terdeteksi di '{kab_np}' (di luar wilayah resmi).")

    return kumpulan_error


