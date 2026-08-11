#!/usr/bin/env python3
import os
import sys
import argparse
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Jika memodifikasi scope ini, hapus file token.pickle terlebih dahulu.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    """Melakukan otentikasi menggunakan OAuth 2.0 dan menghasilkan token."""
    creds = None
    # File token.pickle menyimpan token akses dan refresh pengguna.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Jika tidak ada kredensial yang valid, minta pengguna untuk login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: File 'credentials.json' tidak ditemukan!")
                print("Silakan unduh file konfigurasi OAuth 2.0 Client ID dari Google Cloud Console")
                print("dan letakkan di folder ini dengan nama 'credentials.json'.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Simpan kredensial untuk dijalankan di lain waktu
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            
    return build('drive', 'v3', credentials=creds)

def list_files(service):
    """Mencari semua file yang dimiliki atau dibagikan oleh user."""
    print("Mengambil daftar file dari Google Drive (bisa memakan waktu beberapa saat)...")
    files = []
    page_token = None
    
    # Query untuk mencari file. Kita cari file yang tidak di-trash.
    query = "trashed = false"
    
    try:
        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, owners, permissions)',
                pageToken=page_token,
                pageSize=100
            ).execute()
            
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if not page_token:
                break
    except HttpError as error:
        print(f"Terjadi kesalahan saat memanggil API: {error}")
        sys.exit(1)
        
    return files

def revoke_access(service, target_emails, dry_run=False):
    """Mengecek semua file dan mencabut hak akses untuk daftar email tertentu serta mencatatnya ke revoke.log."""
    files = list_files(service)
    print(f"Total ditemukan {len(files)} file di Drive Anda.\n")
    
    emails_lower = [email.lower().strip() for email in target_emails if email.strip()]
    if not emails_lower:
        print("Tidak ada email target yang valid untuk diproses.")
        return

    revoked_count = 0
    scanned_count = 0
    
    # Buka file log revoke.log untuk mencatat hasil
    log_mode = 'a' if os.path.exists('revoke.log') else 'w'
    with open('revoke.log', log_mode, encoding='utf-8') as log_file:
        log_file.write(f"\n=== Sesi {'Dry Run' if dry_run else 'Revoke'} ===\n")
        
        for file in files:
            file_id = file.get('id')
            file_name = file.get('name')
            
            # Ambil izin akses (permissions) detail untuk file ini
            try:
                file_details = service.files().get(
                    fileId=file_id, 
                    fields='permissions, owners'
                ).execute()
            except HttpError as e:
                continue
                
            permissions = file_details.get('permissions', [])
            owners = file_details.get('owners', [])
            
            for perm in permissions:
                email_address = perm.get('emailAddress', '').lower()
                role = perm.get('role')
                
                if email_address in emails_lower:
                    perm_id = perm.get('id')
                    match_info = f"File: '{file_name}' ({file_id}) | User: {email_address} ({role})"
                    print(f"[MATCH] {match_info}")
                    
                    if dry_run:
                        print(f"        [DRY-RUN] Hak akses akan dicabut.")
                        log_file.write(f"[DRY-RUN MATCH] {match_info}\n")
                        revoked_count += 1
                    else:
                        try:
                            print(f"        Mencabut hak akses...")
                            service.permissions().delete(fileId=file_id, permissionId=perm_id).execute()
                            print(f"        [SUKSES] Hak akses telah dicabut.")
                            log_file.write(f"[REVOKED] {match_info}\n")
                            revoked_count += 1
                        except HttpError as error:
                            print(f"        [GAGAL] Gagal mencabut hak akses: {error}")
                            log_file.write(f"[GAGAL REVOKE] {match_info} - Error: {error}\n")
                            
            scanned_count += 1
            if scanned_count % 50 == 0:
                print(f"Telah memeriksa {scanned_count} file...")

        log_file.write(f"Total: {'Ditemukan' if dry_run else 'Dicabut'} {revoked_count} akses.\n")

    print("\n" + "="*50)
    if dry_run:
        print(f"Selesai (Dry Run). Ditemukan {revoked_count} kecocokan akses. Detail dicatat ke revoke.log.")
    else:
        print(f"Selesai. Berhasil mencabut {revoked_count} hak akses. Detail dicatat ke revoke.log.")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description="Google Drive Access Revoker CLI")
    parser.add_argument(
        '--file',
        default='accounts.txt',
        help='File yang berisi daftar email target (satu email per baris, default: accounts.txt)'
    )
    parser.add_argument(
        '--emails', 
        nargs='+', 
        help='Daftar email langsung dari CLI (opsional, jika tidak ingin memakai file)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Hanya mengecek dan menampilkan file mana saja yang akan dicabut aksesnya tanpa melakukan perubahan'
    )
    
    args = parser.parse_args()
    
    target_emails = []
    
    # Ambil email dari file jika ada
    if os.path.exists(args.file):
        print(f"Membaca daftar email dari file: {args.file}")
        with open(args.file, 'r', encoding='utf-8') as f:
            target_emails = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    else:
        if args.file != 'accounts.txt':
            print(f"Error: File '{args.file}' tidak ditemukan!")
            sys.exit(1)
            
    # Gabungkan dengan email dari argumen CLI jika ada
    if args.emails:
        target_emails.extend(args.emails)
        
    if not target_emails:
        print("Error: Tidak ada email target yang diberikan!")
        print("Silakan buat file 'accounts.txt' yang berisi daftar email, atau gunakan argumen '--emails'.")
        sys.exit(1)
        
    print(f"Daftar email target ({len(target_emails)}):")
    for email in target_emails:
        print(f" - {email}")
    print()

    print("Memulai Google Drive Access Revoker...")
    service = authenticate()
    revoke_access(service, target_emails, dry_run=args.dry_run)

if __name__ == '__main__':
    main()
