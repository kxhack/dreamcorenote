-- 処理済みTikTok動画ID(重複投稿防止)
CREATE TABLE IF NOT EXISTS processed_videos (
  video_id TEXT PRIMARY KEY,
  processed_at TEXT NOT NULL
);

-- 記事本体
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  body_html TEXT NOT NULL,
  location TEXT,
  atmosphere TEXT,
  seo_description TEXT,
  tags TEXT,            -- JSON配列を文字列で保存
  tiktok_url TEXT,
  image_urls TEXT,      -- JSON配列を文字列で保存(R2の公開URL)
  status TEXT NOT NULL DEFAULT 'draft',  -- 'draft' または 'published'
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_status_created
  ON articles (status, created_at DESC);
