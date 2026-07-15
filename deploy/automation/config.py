"""
環境変数の読み込みと共通設定
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- TikTok ---
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "").lstrip("@")
MAX_VIDEOS_PER_RUN = int(os.getenv("MAX_VIDEOS_PER_RUN", "3"))

# --- AI ---
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# --- 画像 ---
FRAME_COUNT = int(os.getenv("FRAME_COUNT", "4"))

# --- Cloudflare D1 ---
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
CF_D1_DATABASE_ID = os.getenv("CF_D1_DATABASE_ID", "")

# --- Cloudflare R2 ---
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
# 例: https://pub-xxxxxxxx.r2.dev (R2バケットの「公開アクセス」有効化時に発行されるURL)
# または独自ドメインを設定した場合はそのURL
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")

# --- 投稿設定 ---
# 'draft' にしておくと記事はD1に保存されるがサイトには表示されない(status='draft')
# 'published' にすると即座にサイトに公開される
POST_STATUS = os.getenv("POST_STATUS", "draft")

# --- 作業用ディレクトリ ---
WORK_DIR = BASE_DIR / "work"
DOWNLOAD_DIR = WORK_DIR / "downloads"
FRAMES_DIR = WORK_DIR / "frames"
LOG_FILE = BASE_DIR / "run.log"

for d in (WORK_DIR, DOWNLOAD_DIR, FRAMES_DIR):
    d.mkdir(parents=True, exist_ok=True)


def validate():
    """必須設定が揃っているかチェックし、不足があれば例外を投げる"""
    missing = []
    if not TIKTOK_USERNAME:
        missing.append("TIKTOK_USERNAME")
    if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if AI_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    for key in ("CF_ACCOUNT_ID", "CF_API_TOKEN", "CF_D1_DATABASE_ID"):
        if not globals()[key]:
            missing.append(key)
    for key in ("R2_BUCKET_NAME", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_PUBLIC_BASE_URL"):
        if not globals()[key]:
            missing.append(key)
    if missing:
        raise RuntimeError(
            f"環境変数に以下の設定が不足しています: {', '.join(missing)}"
        )
