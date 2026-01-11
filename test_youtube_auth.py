#!/usr/bin/env python3
"""Test YouTube authentication - upload scope only"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

creds = Credentials.from_authorized_user_file("youtube_token.json", SCOPES)
print("Token valid:", creds.valid)
print("Has refresh_token:", bool(creds.refresh_token))

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    print("Token refreshed!")
    with open("youtube_token.json", "w") as f:
        f.write(creds.to_json())
    print("Updated token saved")

youtube = build("youtube", "v3", credentials=creds)
print("YouTube service built successfully!")
print("\n✅ Ready for upload!")
