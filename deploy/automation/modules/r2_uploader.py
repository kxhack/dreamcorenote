"""
Cloudflare R2(S3互換API)へ画像をアップロードし、公開URLを返す。
"""
import logging
from pathlib import Path

import boto3

import config

logger = logging.getLogger(__name__)

_endpoint_url = f"https://{config.CF_ACCOUNT_ID}.r2.cloudflarestorage.com"

_client = boto3.client(
    "s3",
    endpoint_url=_endpoint_url,
    aws_access_key_id=config.R2_ACCESS_KEY_ID,
    aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
    region_name="auto",
)


def upload_image(local_path: str, video_id: str) -> str:
    """画像をR2にアップロードし、公開URLを返す"""
    path = Path(local_path)
    key = f"tiktok/{video_id}/{path.name}"

    content_type = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    _client.upload_file(
        str(path),
        config.R2_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    url = f"{config.R2_PUBLIC_BASE_URL}/{key}"
    logger.info("R2アップロード成功: %s", url)
    return url
