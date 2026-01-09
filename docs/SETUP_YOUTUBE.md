# YouTube Credentials Setup Guide

This guide explains how to obtain the necessary credentials (`youtube_client_secret.json`) and generate the token (`youtube_token.json`) required for the Youtube automation tools.

## Prerequisites

- A Google Account (preferably the one managing the YouTube channel).
- Access to [Google Cloud Console](https://console.cloud.google.com/).

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown at the top left and select **"New Project"**.
3. Enter a project name (e.g., `Dhamma-Automation`).
4. Click **"Create"** and wait for the project to be provisioned.
5. Select the newly created project.

## Step 2: Enable APIs

1. In the left sidebar, go to **"APIs & Services" > "Enabled APIs & services"**.
2. Click **"+ ENABLE APIS AND SERVICES"**.
3. Search for **"YouTube Data API v3"** and enable it.
4. Search for **"YouTube Analytics API"** and enable it.

## Step 3: Configure OAuth Consent Screen

1. In the left sidebar, go to **"APIs & Services" > "OAuth consent screen"**.
2. Select **"External"** (unless you are in a Google Workspace organization and want to limit to internal users) and click **"Create"**.
3. Fill in the required information:
    - **App name**: Dhamma Automation (or similar).
    - **User support email**: Your email.
    - **Developer contact information**: Your email.
4. Click **"Save and Continue"**.
5. **Scopes**: Click **"Add or Remove Scopes"** and add the following:
    - `https://www.googleapis.com/auth/youtube.upload`
    - `https://www.googleapis.com/auth/youtube.readonly`
    - `https://www.googleapis.com/auth/yt-analytics.readonly`
6. Click **"Update"**, then **"Save and Continue"**.
7. **Test Users**: Add the email address of the YouTube channel account you want to manage.
8. Click **"Save and Continue"** and review your summary.

## Step 4: Create Credentials

1. In the left sidebar, go to **"APIs & Services" > "Credentials"**.
2. Click **"+ CREATE CREDENTIALS"** and select **"OAuth client ID"**.
3. **Application type**: Select **"Desktop app"**.
4. **Name**: Enter a name (e.g., `Desktop Client`).
5. Click **"Create"**.
6. A pop-up will appear. Click **"DOWNLOAD JSON"**.
7. **Rename the downloaded file to `youtube_client_secret.json`**.
8. Move this file to the root of your `flowbiz-client-dhamma` directory (or the directory where you run the scripts).

## Step 5: Generate Token

The first time you run a script, it will use the `youtube_client_secret.json` to authenticate via the browser and generate a `youtube_token.json`.

1. Run one of the scripts, for example, the KPI reporter:

    ```bash
    python scripts/report_kpi.py --days 7d
    ```

2. A browser window will open asking you to sign in. **Make sure to sign in with the YouTube channel account.**
3. If you see a "Google hasn't verified this app" warning (because your app is in testing mode), click **"Advanced"** > **"Go to [App Name] (unsafe)"**.
4. Click **"Continue"** to grant permissions.
5. Review the requested permissions (Manage your YouTube videos, View YouTube Analytics, etc.) and click **"Continue"**.
6. The script should confirm authentication success.
7. A file named `youtube_token.json` will be created in your directory.

> [!IMPORTANT]
> **Keep these files secret!**
> Never commit `youtube_client_secret.json` or `youtube_token.json` to version control. They should already be in your `.gitignore`.
