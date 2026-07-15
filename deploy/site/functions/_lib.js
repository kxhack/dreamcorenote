export function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function layout({ title, description, body }) {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description || "")}">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div class="wrap">
<header class="site">
  <h1><a href="/">誰もいない場所のブログ</a></h1>
  <p>TikTokで撮影した非日常な場所を紹介しています</p>
</header>
${body}
</div>
</body>
</html>`;
}

export function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("ja-JP", { year: "numeric", month: "long", day: "numeric" });
  } catch {
    return iso;
  }
}
