"""
自分のTikTokプロフィールを yt-dlp でチェックし、
未処理(未投稿)の新着動画を検出・ダウンロードする。

処理済みIDの管理はCloudflare D1側で行うため、
このモジュールはローカルに状態を持たない。

注意:
TikTok公式の「新着動画取得API」は企業審査が必要なため、
ここでは公開プロフィールページを yt-dlp でスクレイピングする方式を採用しています。
TikTok側のサイト仕様変更で動かなくなった場合は
`pip install -U yt-dlp` で最新版に更新してください。
"""
import logging
from pathlib import Path

import yt_dlp

import config

logger = logging.getLogger(__name__)


def _list_profile_video_ids(username: str) -> list[str]:
    """プロフィールページから動画IDの一覧を新しい順で取得(ダウンロードはしない)"""
    profile_url = f"https://www.tiktok.com/@{username}"
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(profile_url, download=False)
    entries = info.get("entries", []) if info else []
    return [e["id"] for e in entries if e.get("id")]


def _download_video(video_id: str) -> dict:
    """動画本体とメタデータ(説明文など)をダウンロードする"""
    video_url = f"https://www.tiktok.com/@{config.TIKTOK_USERNAME}/video/{video_id}"
    out_template = str(config.DOWNLOAD_DIR / f"{video_id}.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "outtmpl": out_template,
        "format": "mp4/best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    video_path = Path(ydl.prepare_filename(info))
    return {
        "id": video_id,
        "url": video_url,
        "description": info.get("description") or info.get("title") or "",
        "hashtags": info.get("tags") or [],
        "video_path": str(video_path),
    }


def get_new_videos(already_processed: set) -> list[dict]:
    """
    未処理の新着動画を最大 MAX_VIDEOS_PER_RUN 件、ダウンロードして返す。
    already_processed: D1から取得した処理済み動画IDの集合
    """
    all_ids = _list_profile_video_ids(config.TIKTOK_USERNAME)
    new_ids = [vid for vid in all_ids if vid not in already_processed]
    new_ids = new_ids[: config.MAX_VIDEOS_PER_RUN]

    if not new_ids:
        logger.info("新着動画はありません")
        return []

    logger.info("新着動画 %d 件を検出: %s", len(new_ids), new_ids)

    videos = []
    for vid in new_ids:
        try:
            videos.append(_download_video(vid))
        except Exception:
            logger.exception("動画 %s のダウンロードに失敗しました", vid)
    return videos
