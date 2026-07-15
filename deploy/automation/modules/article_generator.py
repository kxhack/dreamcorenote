"""
TikTokの説明文・ハッシュタグから、WordPress用のブログ記事を生成する。
AI_PROVIDER の設定に応じて OpenAI / Anthropic を切り替える。
"""
import json
import logging

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """あなたは旅行・散策・非日常スポット紹介ブログのプロ編集者です。
TikTokに投稿された動画の説明文とハッシュタグをもとに、WordPressに掲載する
日本語のブログ記事をSEOを意識して作成します。

出力は必ず以下のキーを持つJSONのみとしてください(説明文やコードブロック記号は不要):
{
  "title": "SEOを意識した記事タイトル(32文字前後)",
  "body_html": "記事本文。<p>や<h2>タグなどを使ったシンプルなHTML。雰囲気のある文章で300〜500字程度。最後に「■場所」「■撮影日」のセクションを含める(不明な場合は「非公開」とする)",
  "location": "動画から推測できる撮影場所(不明なら「不明」)",
  "atmosphere": "その場所の雰囲気を表す一言(例: Liminal Space, 廃墟感, 郷愁 など)",
  "seo_description": "検索結果に表示されるメタディスクリプション(80〜120字)",
  "tags": ["SEOタグを3〜6個の配列で"]
}
"""


def _build_user_prompt(description: str, hashtags: list[str]) -> str:
    tags_str = " ".join(f"#{t}" for t in hashtags) if hashtags else "(なし)"
    return (
        f"【TikTok説明文】\n{description}\n\n"
        f"【ハッシュタグ】\n{tags_str}\n\n"
        "上記をもとに記事を生成してください。"
    )


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text)


def _generate_with_openai(description: str, hashtags: list[str]) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(description, hashtags)},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )
    return json.loads(resp.choices[0].message.content)


def _generate_with_anthropic(description: str, hashtags: list[str]) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_prompt(description, hashtags)}
        ],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return _parse_json_response(text)


def generate_article(description: str, hashtags: list[str]) -> dict:
    """
    戻り値: {title, body_html, location, atmosphere, seo_description, tags}
    """
    if config.AI_PROVIDER == "anthropic":
        article = _generate_with_anthropic(description, hashtags)
    else:
        article = _generate_with_openai(description, hashtags)

    for key in ("title", "body_html", "location", "atmosphere", "seo_description", "tags"):
        article.setdefault(key, "")

    logger.info("記事生成完了: %s", article.get("title"))
    return article
