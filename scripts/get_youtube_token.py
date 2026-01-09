#!/usr/bin/env python3
"""
YouTube Token Generator
Generates youtube_token.json from youtube_client_secret.json
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for Upload and Analytics
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

def main():
    client_secret_file = Path("youtube_client_secret.json")
    token_file = Path("youtube_token.json")

    if not client_secret_file.exists():
        print(f"❌ Error: {client_secret_file} not found!")
        print("Please download your OAuth 2.0 Client ID JSON from Google Cloud Console")
        print(f"and save it as '{client_secret_file}' in the current directory.")
        return

    print(f"🔐 Starting OAuth flow using {client_secret_file}...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
        # Using run_local_server which is standard for desktop apps
        # If it fails to open a browser, it usually prints a link
        creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())

        print(f"\n✅ Success! Token saved to {token_file}")
        print("You can now run your automation scripts.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
