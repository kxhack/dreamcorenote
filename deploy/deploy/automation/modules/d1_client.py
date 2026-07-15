"""
Cloudflare D1 REST APIを使って、
・処理済みTikTok動画IDの記録/確認
・記事データの保存
を行う。
"""
import json
import logging
from datetime import datetime, timezone

import requests

import config

logger = logging.getLogger(__name__)

_API_BASE = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{config.CF_ACCOUNT_ID}/d1/database/{config.CF_D1_DATABASE_ID}/query"
)
_HEADERS = {
    "Authorization": f"Bearer {config.CF_API_TOKEN}",
    "Content-Type": "application/json",
}


def _execute(sql: str, params: list = None) -> list:
    resp = requests.post(
        _API_BASE,
        headers=_HEADERS,
        json={"sql": sql, "params": params or []},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"D1クエリ失敗: {data.get('errors')}")
    # D1 REST APIは result を配列で返す(バッチ実行に対応するため)
    result = data["result"][0]
    return result.get("results", [])


def ensure_schema() -> None:
    """テーブルが存在しなければ作成する(初回実行時の安全策)"""
    _execute(
        """CREATE TABLE IF NOT EXISTS processed_videos (
            video_id TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL
        )"""
    )
    _execute(
        """CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            body_html TEXT NOT NULL,
            location TEXT,
            atmosphere TEXT,
            seo_description TEXT,
            tags TEXT,
            tiktok_url TEXT,
            image_urls TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL
        )"""
    )


def get_processed_ids() -> set:
    rows = _execute("SELECT video_id FROM processed_videos")
    return {row["video_id"] for row in rows}


def mark_processed(video_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    _execute(
        "INSERT OR IGNORE INTO processed_videos (video_id, processed_at) VALUES (?, ?)",
        [video_id, now],
    )


def _slugify(video_id: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{now}-{video_id}"


def insert_article(article: dict, image_urls: list, video: dict) -> str:
    """記事をD1に保存し、生成したslugを返す"""
    slug = _slugify(video["id"])
    now = datetime.now(timezone.utc).isoformat()

    _execute(
        """INSERT INTO articles
           (slug, title, body_html, location, atmosphere, seo_description,
            tags, tiktok_url, image_urls, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            slug,
            article.get("title", ""),
            article.get("body_html", ""),
            article.get("location", ""),
            article.get("atmosphere", ""),
            article.get("seo_description", ""),
            json.dumps(article.get("tags", []), ensure_ascii=False),
            video.get("url", ""),
            json.dumps(image_urls, ensure_ascii=False),
            config.POST_STATUS,
            now,
        ],
    )
    logger.info("D1に記事を保存しました: slug=%s status=%s", slug, config.POST_STATUS)
    return slug
