function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }
  
  function layout({ title, description, body }) {
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
  
  function formatDate(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("ja-JP", { year: "numeric", month: "long", day: "numeric" });
    } catch {
      return iso;
    }
  }
  
  async function renderIndex(env) {
    const { results } = await env.DB.prepare(
      `SELECT slug, title, seo_description, image_urls, created_at
       FROM articles WHERE status = 'published'
       ORDER BY created_at DESC LIMIT 50`
    ).all();
  
    let body;
    if (!results || results.length === 0) {
      body = `<p class="empty">まだ記事がありません。</p>`;
    } else {
      body = results.map((row) => {
        let images = [];
        try { images = JSON.parse(row.image_urls || "[]"); } catch {}
        const thumb = images[0]
          ? `<img src="${escapeHtml(images[0])}" alt="${escapeHtml(row.title)}" loading="lazy">`
          : "";
        return `<div class="card">
          <h2><a href="/article/${encodeURIComponent(row.slug)}">${escapeHtml(row.title)}</a></h2>
          <div class="meta">${formatDate(row.created_at)}</div>
          ${thumb}
          <p class="excerpt">${escapeHtml(row.seo_description || "")}</p>
        </div>`;
      }).join("\n");
    }
  
    return layout({
      title: "誰もいない場所のブログ",
      description: "TikTokで撮影した非日常な場所を紹介するブログです。",
      body,
    });
  }
  
  async function renderArticle(env, slug) {
    const row = await env.DB.prepare(
      `SELECT * FROM articles WHERE slug = ? AND status = 'published' LIMIT 1`
    ).bind(slug).first();
  
    if (!row) return null;
  
    let images = [], tags = [];
    try { images = JSON.parse(row.image_urls || "[]"); } catch {}
    try { tags = JSON.parse(row.tags || "[]"); } catch {}
  
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
  
    return layout({ title: row.title, description: row.seo_description, body });
  }
  
  export default {
    async fetch(request, env) {
      const url = new URL(request.url);
      const path = url.pathname;
  
      if (path === "/") {
        const html = await renderIndex(env);
        return new Response(html, { headers: { "content-type": "text/html; charset=UTF-8" } });
      }
  
      if (path.startsWith("/article/")) {
        const slug = decodeURIComponent(path.replace("/article/", ""));
        const html = await renderArticle(env, slug);
        if (!html) return new Response("Not Found", { status: 404 });
        return new Response(html, { headers: { "content-type": "text/html; charset=UTF-8" } });
      }
  
      // それ以外(style.cssなど)は静的ファイルとして返す
      return env.ASSETS.fetch(request);
    },
  };