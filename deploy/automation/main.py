"""
TikTok自動投稿システム メイン処理(Cloudflareのみ完結版)

  自分のTikTok新着動画を検出(処理済み判定はCloudflare D1)
        ↓
  動画URL・説明文を取得
        ↓
  AIで記事生成(タイトル/本文/撮影場所/雰囲気/SEO)
        ↓
  動画から画像を数枚抽出
        ↓
  画像をCloudflare R2にアップロード
        ↓
  記事をCloudflare D1に保存 → Cloudflare Pagesが自動的に表示

GitHub Actions等から定期実行することを想定した1回実行型のスクリプトです。
"""
import logging
import shutil
import sys
import traceback
from pathlib import Path

import config
from modules import tiktok_monitor, article_generator, image_extractor, d1_client, r2_uploader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")


def process_video(video: dict) -> None:
    video_id = video["id"]
    logger.info("=== 動画 %s の処理を開始 ===", video_id)

    # 1. 記事生成
    article = article_generator.generate_article(
        description=video["description"],
        hashtags=video.get("hashtags", []),
    )

    # 2. 画像抽出
    frame_paths = image_extractor.extract_frames(video["video_path"], video_id)

    # 3. R2へ画像アップロード
    image_urls = [r2_uploader.upload_image(p, video_id) for p in frame_paths]

    # 4. D1へ記事保存
    slug = d1_client.insert_article(article, image_urls, video)
    logger.info("記事保存完了: slug=%s", slug)

    # 5. 処理済みとして記録
    d1_client.mark_processed(video_id)

    # 6. 一時ファイル削除
    _cleanup(video_id, video["video_path"])


def _cleanup(video_id: str, video_path: str) -> None:
    try:
        Path(video_path).unlink(missing_ok=True)
        frame_dir = config.FRAMES_DIR / video_id
        if frame_dir.exists():
            shutil.rmtree(frame_dir)
    except Exception:
        logger.warning("一時ファイルの削除に失敗しました(無視して続行)", exc_info=True)


def main() -> int:
    try:
        config.validate()
    except RuntimeError as e:
        logger.error(str(e))
        return 1

    d1_client.ensure_schema()

    logger.info("新着動画のチェックを開始します(@%s)", config.TIKTOK_USERNAME)
    already_processed = d1_client.get_processed_ids()
    videos = tiktok_monitor.get_new_videos(already_processed)

    if not videos:
        logger.info("処理対象の新着動画はありませんでした")
        return 0

    success, failed = 0, 0
    for video in videos:
        try:
            process_video(video)
            success += 1
            except Exception:
            failed += 1
            logger.error("動画 %s の処理中にエラーが発生しました:\n%s",
            video.get("id"), traceback.format_exc())
            # 失敗した動画も処理済みとして記録し、無限リトライを防ぐ
            try:
                d1_client.mark_processed(video["id"])
                logger.info("動画 %s を失敗として処理済み登録しました(スキップ対象)", video["id"])
            except Exception:
                logger.warning("処理済み登録にも失敗しました: %s", video["id"])

    logger.info("処理完了: 成功 %d件 / 失敗 %d件", success, failed)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
