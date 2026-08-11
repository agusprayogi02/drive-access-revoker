# Google Drive Access Revoker CLI

Script CLI berbasis Python untuk mendeteksi dan mencabut (revoke) hak akses Google Drive terhadap beberapa email target sekaligus secara massal (bulk). Berguna untuk perusahaan/instansi yang ingin membersihkan akses file setelah masa magang atau kontrak kerja karyawan selesai.

## Fitur Utama

- **Mass Revocation**: Mencabut hak akses dari daftar email yang didefinisikan di dalam file teks.
- **Dry-Run Mode**: Simulasi untuk mendeteksi file apa saja yang memiliki kecocokan akses sebelum benar-benar dihapus.
- **Log System**: Mencatat semua riwayat deteksi dan pencabutan hak akses ke dalam file log terpisah (`revoke.log`).
- **OAuth 2.0 Client Authentication**: Aman karena langsung menggunakan otentikasi resmi API Google Cloud Console.

---

## Persiapan & Instalasi

### 1. Klon & Install Dependensi
Pastikan python dan virtual environment sudah siap, lalu pasang library Google API Client:
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Dapatkan `credentials.json` dari Google Cloud Console
Untuk menghubungkan script dengan Google Drive Anda:
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat proyek baru atau pilih proyek yang sudah ada.
3. Cari **Google Drive API** di kolom pencarian atas, pilih, lalu klik **Enable** (Aktifkan).
4. Masuk ke menu **APIs & Services** > **OAuth consent screen**:
   - Jika Anda menggunakan Google Workspace Perusahaan, pilih User Type **Internal**.
   - Isi informasi aplikasi yang wajib (App name, User support email, Developer contact info), lalu klik Save.
5. Masuk ke **APIs & Services** > **Credentials**:
   - Klik **+ Create Credentials** di bagian atas, pilih **OAuth client ID**.
   - Pilih Application type: **Desktop App**.
   - Beri nama (misal: `Drive Revoker`), lalu klik **Create**.
6. Unduh file konfigurasi JSON tersebut.
7. Pindahkan/salin file JSON yang diunduh ke folder project ini dan ubah namanya menjadi **`credentials.json`**.

---

## Cara Penggunaan

### 1. Tentukan Email Target (`accounts.txt`)
Buat sebuah file teks bernama **`accounts.txt`** di folder yang sama dengan script. Tuliskan daftar email target yang ingin dicabut hak aksesnya (satu email per baris):

```text
anak.magang1@perusahaan.com
anak.magang2@perusahaan.com
```

### 2. Jalankan Mode Uji Coba (`--dry-run`)
Sebelum benar-benar menghapus hak akses, Anda disarankan menjalankan mode Dry-Run terlebih dahulu untuk melihat file apa saja yang terdeteksi memiliki sharing link ke email target.

```bash
python3 revoker.py --dry-run
```
*Hasil pencarian dry-run akan tampil di terminal dan tersimpan di file `revoke.log`.*

### 3. Eksekusi Pencabutan Akses
Jika hasil uji coba di atas sudah sesuai, jalankan perintah di bawah ini untuk mencabut hak akses secara nyata dari Google Drive Anda:

```bash
python3 revoker.py
```

### 4. Custom File Target (Opsional)
Jika Anda ingin menggunakan file selain `accounts.txt`, gunakan parameter `--file`:
```bash
python3 revoker.py --file email_list_lain.txt
```

---

## Log Aktivitas (`revoke.log`)

Setiap kali script dijalankan, riwayatnya akan dicatat di file `revoke.log`:
- `[DRY-RUN MATCH]` : Menandakan kecocokan email target yang ditemukan selama uji coba.
- `[REVOKED]`       : Menandakan hak akses file yang berhasil dicabut secara permanen.
- `[GAGAL REVOKE]`  : Menandakan adanya error saat pencabutan (misal: kendala koneksi atau hak akses akun).
