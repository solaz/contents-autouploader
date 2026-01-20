"""YouTube upload service using Google API."""

import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import Settings, settings
from src.utils.helpers import ensure_dir


# OAuth2 scopes for YouTube upload
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeService:
    """Service for uploading videos to YouTube."""

    def __init__(self, config: Settings | None = None):
        self.config = config or settings()
        self.youtube_config = self.config.youtube
        self._service = None
        self._credentials_path = Path.home() / ".config" / "contents-autouploader" / "youtube_credentials.json"

    def _get_credentials(self) -> Credentials:
        """Get or refresh YouTube API credentials."""
        ensure_dir(self._credentials_path.parent)

        # Check for existing credentials
        if self._credentials_path.exists():
            with open(self._credentials_path) as f:
                creds_data = json.load(f)
            credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
            if credentials.valid:
                return credentials
            if credentials.expired and credentials.refresh_token:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
                self._save_credentials(credentials)
                return credentials

        # Need to authenticate
        client_config = {
            "installed": {
                "client_id": self.config.youtube_client_id,
                "client_secret": self.config.youtube_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/"],
            }
        }

        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        credentials = flow.run_local_server(port=8080)
        self._save_credentials(credentials)

        return credentials

    def _save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to file."""
        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }
        with open(self._credentials_path, "w") as f:
            json.dump(creds_data, f)

    def _get_service(self):
        """Get YouTube API service."""
        if self._service is None:
            credentials = self._get_credentials()
            self._service = build("youtube", "v3", credentials=credentials)
        return self._service

    def upload(
        self,
        video_path: Path | str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        category_id: str | None = None,
        privacy_status: str | None = None,
        thumbnail_path: Path | str | None = None,
    ) -> str:
        """Upload a video to YouTube.

        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: 'public', 'private', or 'unlisted'
            thumbnail_path: Optional path to thumbnail image

        Returns:
            Video ID of the uploaded video
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        tags = tags or self.youtube_config.default_tags
        category_id = category_id or self.youtube_config.category_id
        privacy_status = privacy_status or self.youtube_config.privacy_status

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        service = self._get_service()

        # Upload video
        media = MediaFileUpload(
            str(video_path),
            chunksize=1024 * 1024,  # 1MB chunks
            resumable=True,
            mimetype="video/mp4",
        )

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"Upload progress: {progress}%")

        video_id = response["id"]
        print(f"Video uploaded successfully: https://www.youtube.com/watch?v={video_id}")

        # Upload thumbnail if provided
        if thumbnail_path:
            self.set_thumbnail(video_id, thumbnail_path)

        return video_id

    def set_thumbnail(self, video_id: str, thumbnail_path: Path | str) -> None:
        """Set thumbnail for a video.

        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
        """
        thumbnail_path = Path(thumbnail_path)
        if not thumbnail_path.exists():
            raise FileNotFoundError(f"Thumbnail file not found: {thumbnail_path}")

        service = self._get_service()

        media = MediaFileUpload(
            str(thumbnail_path),
            mimetype="image/png",
        )

        service.thumbnails().set(
            videoId=video_id,
            media_body=media,
        ).execute()

        print(f"Thumbnail set for video: {video_id}")

    def get_video_url(self, video_id: str) -> str:
        """Get the YouTube URL for a video ID."""
        return f"https://www.youtube.com/watch?v={video_id}"

    def check_upload_status(self, video_id: str) -> dict:
        """Check the processing status of an uploaded video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with status information
        """
        service = self._get_service()

        response = service.videos().list(
            part="status,processingDetails",
            id=video_id,
        ).execute()

        if response["items"]:
            video = response["items"][0]
            return {
                "upload_status": video["status"].get("uploadStatus"),
                "privacy_status": video["status"].get("privacyStatus"),
                "processing_status": video.get("processingDetails", {}).get("processingStatus"),
            }

        return {"error": "Video not found"}
