#!/usr/bin/env python3
"""
Google Drive utility — sync files between local backend/ and the shared Drive folder.

Target folder: https://drive.google.com/drive/folders/19JY_X26pjwDYoe3iKuZ1AJTgRh6Dt8Yr

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  list
      Show all files in the Drive folder (recursive).

  download <filename>
      Download a file by name. The local path mirrors the Drive folder
      structure (e.g. data/samples/lesson1.mp3 in Drive → saved to
      backend/data/samples/lesson1.mp3 locally).

  download-all [extension]
      Download all files with the given extension (default: .mp3).
      Each file is saved mirroring the Drive folder structure locally.
      Example: python scripts/gdrive.py download-all .json

  upload <local-path>
      Upload a local file to Drive, mirroring the local folder structure.
      Path is relative to backend/ (e.g. data/samples/lesson1.json).
      If a file with the same name already exists in Drive it is updated.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python scripts/gdrive.py list
  python scripts/gdrive.py download lesson1.mp3
  python scripts/gdrive.py download lesson1_pinyin.json
  python scripts/gdrive.py download-all .json
  python scripts/gdrive.py upload data/samples/lesson1.json
  python scripts/gdrive.py upload data/samples/lesson1_en.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 FIRST-TIME AUTH SETUP (OAuth2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable "Google Drive API"
  3. APIs & Services → Credentials → Create Credentials → OAuth client ID
     → Application type: Desktop app → Download JSON
  4. Save it as: backend/credentials/oauth_client.json
  5. On first run, a URL is printed — open it in your browser, approve
     access, then paste the redirect URL back into the terminal.
     Token is saved to backend/credentials/token.json for future runs.
"""

import sys
import mimetypes
from pathlib import Path
from urllib.parse import urlparse, parse_qs

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
                str(OAUTH_CLIENT_PATH), SCOPES,
                redirect_uri="http://localhost",
            )
            auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
            print("\n1. Open this URL in your browser:")
            print(f"\n   {auth_url}\n")
            print("2. After approving, your browser will redirect to http://localhost/...")
            print("   (the page won't load — that's expected)")
            print("3. Copy the full URL from the browser's address bar and paste it here.\n")
            redirected = input("Paste the redirect URL: ").strip()
            code = parse_qs(urlparse(redirected).query).get("code", [None])[0]
            if not code:
                print("Error: could not extract authorization code from URL.")
                sys.exit(1)
            flow.fetch_token(code=code)
            creds = flow.credentials
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


def get_or_create_folder(service, name: str, parent_id: str) -> str:
    """Return the Drive folder ID for `name` inside `parent_id`, creating it if needed."""
    existing = service.files().list(
        q=f"'{parent_id}' in parents and name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)",
    ).execute().get("files", [])
    if existing:
        return existing[0]["id"]
    folder = service.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        fields="id",
    ).execute()
    return folder["id"]


def resolve_drive_folder(service, relative_parts: list[str]) -> str:
    """Walk (and create if needed) a folder path inside FOLDER_ID, return the leaf folder ID."""
    folder_id = FOLDER_ID
    for part in relative_parts:
        folder_id = get_or_create_folder(service, part, folder_id)
    return folder_id


def upload_file(service, local_path: Path, relative_to: Path | None = None) -> str:
    """
    Upload local_path to Drive, mirroring its folder structure relative to `relative_to`.
    If relative_to is given, the file is placed in the matching subfolder inside FOLDER_ID.
    """
    name = local_path.name
    mime = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"

    # Resolve target folder in Drive
    if relative_to:
        try:
            parts = list(local_path.relative_to(relative_to).parent.parts)
        except ValueError:
            parts = []
    else:
        parts = []
    target_folder_id = resolve_drive_folder(service, parts) if parts else FOLDER_ID

    # Check if a file with the same name already exists (update instead of duplicate)
    existing = service.files().list(
        q=f"'{target_folder_id}' in parents and name='{name}' and trashed=false",
        fields="files(id, name)",
    ).execute().get("files", [])

    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)

    if existing:
        file_id = existing[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  Updated: {'/'.join(parts + [name])} (id={file_id})")
    else:
        result = service.files().create(
            body={"name": name, "parents": [target_folder_id]},
            media_body=media,
            fields="id",
        ).execute()
        file_id = result["id"]
        print(f"  Uploaded: {'/'.join(parts + [name])} (id={file_id})")

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


BACKEND_ROOT = Path(__file__).parent.parent


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
    # Mirror Drive's relative path locally under backend root
    relative_path = Path(match["name"])
    dest_dir = BACKEND_ROOT / relative_path.parent
    path = download_file(service, match["id"], relative_path.name, dest_dir)
    print(f"Saved to {path}")


def cmd_download_all(extension: str = ".mp3"):
    service = get_service()
    files = [f for f in list_files(service) if f["name"].endswith(extension)]
    if not files:
        print(f"No {extension} files found in Drive folder.")
        return
    print(f"Downloading {len(files)} file(s) ...")
    for f in files:
        relative_path = Path(f["name"])
        dest_dir = BACKEND_ROOT / relative_path.parent
        download_file(service, f["id"], relative_path.name, dest_dir)
    print("Done.")


def cmd_upload(local_path_str: str):
    local_path = Path(local_path_str)
    if not local_path.exists():
        # Try resolving relative to backend root
        local_path = Path(__file__).parent.parent / local_path_str
    if not local_path.exists():
        print(f"Error: '{local_path_str}' does not exist.")
        sys.exit(1)
    backend_root = Path(__file__).parent.parent
    service = get_service()
    upload_file(service, local_path.resolve(), relative_to=backend_root.resolve())


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
