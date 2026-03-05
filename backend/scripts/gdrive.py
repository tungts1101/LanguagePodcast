#!/usr/bin/env python3
"""
Google Drive utility for uploading and downloading audio samples.

Target folder: https://drive.google.com/drive/folders/19JY_X26pjwDYoe3iKuZ1AJTgRh6Dt8Yr

Authentication (OAuth2 — uses your Google account's storage quota):
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable "Google Drive API"
  3. APIs & Services → Credentials → Create Credentials → OAuth client ID
     → Application type: Desktop app → Download JSON
  4. Save the downloaded file as: backend/credentials/oauth_client.json
  5. First run will print a URL — open it in your browser, approve access,
     then paste the authorization code back into the terminal.
     A token is saved to backend/credentials/token.json for future runs.

Usage:
  # List files in the folder
  python scripts/gdrive.py list

  # Download a file by name
  python scripts/gdrive.py download lesson1.mp3

  # Download all mp3 files
  python scripts/gdrive.py download-all

  # Upload a file
  python scripts/gdrive.py upload data/samples/lesson1.json
"""

import sys
import mimetypes
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ── Config ────────────────────────────────────────────────────────────────────

FOLDER_ID         = "19JY_X26pjwDYoe3iKuZ1AJTgRh6Dt8Yr"
SCOPES            = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_DIR   = Path(__file__).parent.parent / "credentials"
OAUTH_CLIENT_PATH = CREDENTIALS_DIR / "oauth_client.json"
TOKEN_PATH        = CREDENTIALS_DIR / "token.json"
SAMPLES_DIR       = Path(__file__).parent.parent / "data" / "samples"

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_service():
    if not OAUTH_CLIENT_PATH.exists():
        print(f"Error: OAuth client file not found at {OAUTH_CLIENT_PATH}")
        print("See the docstring in this file for setup instructions.")
        sys.exit(1)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(OAUTH_CLIENT_PATH), SCOPES
            )
            # run_console: prints a URL to open in browser, then paste the code back
            creds = flow.run_console()
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)

# ── Operations ────────────────────────────────────────────────────────────────

def list_files_in_folder(service, folder_id: str) -> list[dict]:
    """Return all items (files + subfolders) directly inside a folder."""
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, size, mimeType, modifiedTime)",
        orderBy="name",
    ).execute()
    return results.get("files", [])


def list_files(service, folder_id: str = FOLDER_ID, prefix: str = "") -> list[dict]:
    """Recursively return all files under folder_id with their relative path as 'name'."""
    items = list_files_in_folder(service, folder_id)
    files = []
    for item in items:
        relative_name = f"{prefix}{item['name']}"
        if item["mimeType"] == "application/vnd.google-apps.folder":
            files.extend(list_files(service, item["id"], prefix=f"{relative_name}/"))
        else:
            files.append({**item, "name": relative_name})
    return files


def download_file(service, file_id: str, file_name: str, dest_dir: Path) -> Path:
    """Download a single file to dest_dir, return the local path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file_name

    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            pct = int(status.progress() * 100)
            print(f"\r  {file_name}: {pct}%", end="", flush=True)
    print()
    return dest_path


def upload_file(service, local_path: Path, dest_name: str | None = None) -> str:
    """Upload a local file to the target Drive folder, return the file ID."""
    name = dest_name or local_path.name
    mime = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"

    # Check if a file with the same name already exists (update instead of duplicate)
    existing = service.files().list(
        q=f"'{FOLDER_ID}' in parents and name='{name}' and trashed=false",
        fields="files(id, name)",
    ).execute().get("files", [])

    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)

    if existing:
        file_id = existing[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  Updated: {name} (id={file_id})")
    else:
        metadata = {"name": name, "parents": [FOLDER_ID]}
        result = service.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()
        file_id = result["id"]
        print(f"  Uploaded: {name} (id={file_id})")

    return file_id

# ── CLI ───────────────────────────────────────────────────────────────────────

def cmd_list():
    service = get_service()
    files = list_files(service)
    if not files:
        print("Folder is empty.")
        return
    print(f"{'Name':<40} {'Size':>10}  {'Modified'}")
    print("-" * 70)
    for f in files:
        size = f.get("size", "-")
        size_str = f"{int(size):,}" if size != "-" else "-"
        print(f"{f['name']:<40} {size_str:>10}  {f['modifiedTime'][:10]}")


def cmd_download(file_name: str):
    service = get_service()
    files = list_files(service)
    # Match by full relative path or just the base filename
    match = next(
        (f for f in files if f["name"] == file_name or Path(f["name"]).name == file_name),
        None,
    )
    if not match:
        print(f"Error: '{file_name}' not found in Drive folder.")
        print("Run 'python scripts/gdrive.py list' to see available files.")
        sys.exit(1)
    path = download_file(service, match["id"], Path(match["name"]).name, SAMPLES_DIR)
    print(f"Saved to {path}")


def cmd_download_all(extension: str = ".mp3"):
    service = get_service()
    files = [f for f in list_files(service) if f["name"].endswith(extension)]
    if not files:
        print(f"No {extension} files found in Drive folder.")
        return
    print(f"Downloading {len(files)} file(s) to {SAMPLES_DIR} ...")
    for f in files:
        download_file(service, f["id"], Path(f["name"]).name, SAMPLES_DIR)
    print("Done.")


def cmd_upload(local_path_str: str):
    local_path = Path(local_path_str)
    if not local_path.exists():
        print(f"Error: '{local_path}' does not exist.")
        sys.exit(1)
    service = get_service()
    upload_file(service, local_path)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()
    elif cmd == "download" and len(sys.argv) == 3:
        cmd_download(sys.argv[2])
    elif cmd == "download-all":
        ext = sys.argv[2] if len(sys.argv) > 2 else ".mp3"
        cmd_download_all(ext)
    elif cmd == "upload" and len(sys.argv) == 3:
        cmd_upload(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
