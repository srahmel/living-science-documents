import io
import json
import tempfile
from django.urls import reverse
from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

User = get_user_model()


def make_png_bytes(size=(16, 16), color=(255, 0, 0, 255)):
    bio = io.BytesIO()
    img = Image.new("RGBA", size, color)
    img.save(bio, format="PNG")
    return bio.getvalue()


def api_client_with_user():
    client = APIClient()
    user = User.objects.create_user(username="uploader", email="uploader@example.com", password="pass12345")
    client.force_authenticate(user=user)
    return client, user


@override_settings(MEDIA_ROOT=tempfile.gettempdir(), REQUIRE_CLAMAV_FOR_UPLOAD=False)
def test_upload_png_success_without_clamav(db):
    client, _ = api_client_with_user()
    url = "/api/publications/attachments/upload-image/"
    data = make_png_bytes()
    file = SimpleUploadedFile("test.png", data, content_type="image/png")
    resp = client.post(url, {"file": file}, format="multipart")
    assert resp.status_code == status.HTTP_201_CREATED, resp.content
    payload = resp.json()
    # required keys
    for k in ["id", "url", "mime", "size", "width", "height", "checksum_sha256", "w", "h", "hash"]:
        assert k in payload
    assert payload["mime"] == "image/png"
    assert payload["width"] >= 1 and payload["height"] >= 1
    assert payload["w"] == payload["width"]
    assert payload["h"] == payload["height"]
    assert payload["hash"] == payload["checksum_sha256"]


@override_settings(MEDIA_ROOT=tempfile.gettempdir(), REQUIRE_CLAMAV_FOR_UPLOAD=False)
def test_upload_svg_success_without_clamav(db):
    client, _ = api_client_with_user()
    url = "/api/publications/attachments/upload-image/"
    svg = b"<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><rect width='10' height='10' fill='red'/></svg>"
    file = SimpleUploadedFile("test.svg", svg, content_type="image/svg+xml")
    resp = client.post(url, {"file": file}, format="multipart")
    assert resp.status_code == status.HTTP_201_CREATED, resp.content
    payload = resp.json()
    assert payload["mime"] == "image/svg+xml"
    # width/height may be None for SVG
    assert "width" in payload and "height" in payload
    assert "hash" in payload


@override_settings(MEDIA_ROOT=tempfile.gettempdir(), REQUIRE_CLAMAV_FOR_UPLOAD=True, CLAMAV_HOST=None, CLAMAV_PORT=None)
def test_upload_fails_when_clamav_not_configured(db):
    client, _ = api_client_with_user()
    url = "/api/publications/attachments/upload-image/"
    data = make_png_bytes()
    file = SimpleUploadedFile("test.png", data, content_type="image/png")
    resp = client.post(url, {"file": file}, format="multipart")
    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Virus scanning not configured" in resp.json().get("error", "")


@override_settings(MEDIA_ROOT=tempfile.gettempdir(), REQUIRE_CLAMAV_FOR_UPLOAD=True, CLAMAV_HOST="127.0.0.1", CLAMAV_PORT=1)
def test_upload_fails_when_clamav_errors(db):
    client, _ = api_client_with_user()
    url = "/api/publications/attachments/upload-image/"
    data = make_png_bytes()
    file = SimpleUploadedFile("test.png", data, content_type="image/png")
    resp = client.post(url, {"file": file}, format="multipart")
    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Virus scan failed" in resp.json().get("error", "")


@override_settings(MEDIA_ROOT=tempfile.gettempdir(), REQUIRE_CLAMAV_FOR_UPLOAD=False, MAX_UPLOAD_IMAGE_SIZE_MB=0)
def test_upload_rejects_too_large(db):
    client, _ = api_client_with_user()
    url = "/api/publications/attachments/upload-image/"
    # any non-empty file will exceed 0 MB
    data = make_png_bytes()
    file = SimpleUploadedFile("big.png", data, content_type="image/png")
    resp = client.post(url, {"file": file}, format="multipart")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "File too large" in resp.json().get("error", "")


@override_settings(MEDIA_ROOT=tempfile.gettempdir(), REQUIRE_CLAMAV_FOR_UPLOAD=False)
def test_upload_rejects_unsupported_mime(db):
    client, _ = api_client_with_user()
    url = "/api/publications/attachments/upload-image/"
    file = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")
    resp = client.post(url, {"file": file}, format="multipart")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported image MIME type" in resp.json().get("error", "")
