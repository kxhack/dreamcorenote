import { layout, escapeHtml, formatDate } from "../_lib.js";

export async function onRequestGet(context) {
  const { env, params } = context;
  const slug = params.slug;

  const row = await env.DB.prepare(
    `SELECT * FROM articles WHERE slug = ? AND status = 'published' LIMIT 1`
  )
    .bind(slug)
    .first();

  if (!row) {
    return new Response(
      layout({
        title: "記事が見つかりません",
        body: `<p class="empty">お探しの記事は見つかりませんでした。</p><a class="back" href="/">← 一覧へ戻る</a>`,
      }),
      { status: 404, headers: { "content-type": "text/html; charset=UTF-8" } }
    );
  }

  let images = [];
  let tags = [];
  try {
    images = JSON.parse(row.image_urls || "[]");
  } catch {
    images = [];
  }
  try {
    tags = JSON.parse(row.tags || "[]");
  } catch {
    tags = [];
  }

  const imagesHtml = images
    .map((url) => `<img src="${escapeHtml(url)}" alt="${escapeHtml(row.title)}" loading="lazy">`)
    .join("\n");

  const tagsHtml = tags.length
    ? `<div class="tags">${tags.map((t) => `<span>#${escapeHtml(t)}</span>`).join("")}</div>`
    : "";

  const tiktokLink = row.tiktok_url
    ? `<p><a href="${escapeHtml(row.tiktok_url)}" target="_blank" rel="noopener">TikTokはこちら</a></p>`
    : "";

  const body = `<article class="post">
    <h1>${escapeHtml(row.title)}</h1>
    <div class="meta">${formatDate(row.created_at)}${row.location ? " ・ " + escapeHtml(row.location) : ""}</div>
    ${imagesHtml}
    <div class="body">${row.body_html || ""}</div>
    ${tiktokLink}
    ${tagsHtml}
    <a class="back" href="/">← 一覧へ戻る</a>
  </article>`;

  const html = layout({
    title: row.title,
    description: row.seo_description,
    body,
  });

  return new Response(html, {
    headers: { "content-type": "text/html; charset=UTF-8" },
  });
}
