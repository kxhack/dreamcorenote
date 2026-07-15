import { layout, escapeHtml, formatDate } from "./_lib.js";

export async function onRequestGet(context) {
  const { env } = context;

  const { results } = await env.DB.prepare(
    `SELECT slug, title, seo_description, image_urls, created_at
     FROM articles
     WHERE status = 'published'
     ORDER BY created_at DESC
     LIMIT 50`
  ).all();

  let body;
  if (!results || results.length === 0) {
    body = `<p class="empty">まだ記事がありません。</p>`;
  } else {
    body = results
      .map((row) => {
        let images = [];
        try {
          images = JSON.parse(row.image_urls || "[]");
        } catch {
          images = [];
        }
        const thumb = images[0]
          ? `<img src="${escapeHtml(images[0])}" alt="${escapeHtml(row.title)}" loading="lazy">`
          : "";
        return `<div class="card">
          <h2><a href="/article/${encodeURIComponent(row.slug)}">${escapeHtml(row.title)}</a></h2>
          <div class="meta">${formatDate(row.created_at)}</div>
          ${thumb}
          <p class="excerpt">${escapeHtml(row.seo_description || "")}</p>
        </div>`;
      })
      .join("\n");
  }

  const html = layout({
    title: "誰もいない場所のブログ",
    description: "TikTokで撮影した非日常な場所を紹介するブログです。",
    body,
  });

  return new Response(html, {
    headers: { "content-type": "text/html; charset=UTF-8" },
  });
}
