from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    # Gunakan credentials.json yang sudah kamu isi
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    creds = flow.run_local_server(port=0)  # Ini akan buka browser

    # Simpan token
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print("Token berhasil disimpan di token.json")

if __name__ == '__main__':
    main()
