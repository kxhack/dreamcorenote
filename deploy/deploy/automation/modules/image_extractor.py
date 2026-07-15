"""
ffmpeg を使って動画から均等な間隔で静止画を抽出する。
サーバーに ffmpeg / ffprobe がインストールされている必要がある。
"""
import logging
import subprocess
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def _get_duration(video_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def extract_frames(video_path: str, video_id: str, count: int = None) -> list[str]:
    count = count or config.FRAME_COUNT
    duration = _get_duration(video_path)

    out_dir = config.FRAMES_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 動画の最初と最後を避けて、間隔を空けたタイムスタンプを決める
    margin = duration * 0.1
    usable = max(duration - 2 * margin, 0.1)
    step = usable / max(count - 1, 1) if count > 1 else usable / 2

    frame_paths = []
    for i in range(count):
        timestamp = margin + step * i
        out_path = out_dir / f"frame_{i+1}.jpg"
        subprocess.run(
            [
                "ffmpeg", "-y", "-ss", f"{timestamp:.2f}",
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                str(out_path),
            ],
            capture_output=True, check=True,
        )
        frame_paths.append(str(out_path))

    logger.info("画像 %d 枚を抽出しました: %s", len(frame_paths), out_dir)
    return frame_paths
