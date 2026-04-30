"""
Google Places API (New) で複数エリア×複数業種を検索し、
営業リスト index.html を生成するスクリプト

フィルター条件:
  - WebサイトURLが登録されていない
  - レビュー数 MIN_REVIEW_COUNT 件以上

2025年3月〜 新料金体系:
  - Basic SKU  : displayName / rating / userRatingCount / formattedAddress
  - Advanced SKU (Contact): websiteUri  ← サイトなし判定に必須
"""

import json
import os
import time
import urllib.parse
from datetime import datetime

import requests

# ═══════════════════════════════════════════════════════
#  API キー
# ═══════════════════════════════════════════════════════
PLACES_API_KEY = os.environ.get("PLACES_API_KEY", "AIzaSyCbbtEs5nch9n8LT663LC04ISju4duBgNc")

MIN_REVIEW_COUNT = 20
OUTPUT_FILE = "index.html"

# ═══════════════════════════════════════════════════════
#  業種リスト（英語エリア用）
# ═══════════════════════════════════════════════════════
BUSINESS_TYPES_EN = [
    {"label": "Cafe",         "search_mode": "text", "text_query": "cafe coffee shop"},
    {"label": "Dentist",      "search_mode": "text", "text_query": "dentist dental clinic"},
    {"label": "Chiropractor", "search_mode": "text", "text_query": "chiropractor"},
    {"label": "Music School", "search_mode": "text", "text_query": "piano lessons music school"},
    {"label": "Builder",      "search_mode": "text", "text_query": "builder renovation"},
    {"label": "Pet Grooming", "search_mode": "text", "text_query": "pet grooming salon"},
    {"label": "Vet",          "search_mode": "text", "text_query": "veterinarian vet clinic"},
]

# ═══════════════════════════════════════════════════════
#  業種リスト（日本語エリア用）
# ═══════════════════════════════════════════════════════
BUSINESS_TYPES_JA = [
    {"label": "カフェ",       "search_mode": "text", "text_query": "カフェ"},
    {"label": "歯科医院",     "search_mode": "text", "text_query": "歯科 歯医者"},
    {"label": "接骨院・整体", "search_mode": "text", "text_query": "整体 接骨院"},
    {"label": "ピアノ教室",   "search_mode": "text", "text_query": "ピアノ教室"},
    {"label": "工務店",       "search_mode": "text", "text_query": "工務店 リフォーム"},
    {"label": "ペットサロン", "search_mode": "text", "text_query": "ペットサロン トリミング"},
    {"label": "動物病院",     "search_mode": "text", "text_query": "動物病院 ペットクリニック"},
]

# ═══════════════════════════════════════════════════════
#  検索エリアリスト
# ═══════════════════════════════════════════════════════
SEARCH_LOCATIONS = [
    {
        "name":           "Melbourne",
        "latitude":       -37.8136,
        "longitude":      144.9631,
        "radius_m":       10000,
        "business_types": BUSINESS_TYPES_EN,
    },
    {
        "name":           "広島",
        "latitude":       34.3853,
        "longitude":      132.4553,
        "radius_m":       1500,
        "business_types": BUSINESS_TYPES_JA,
    },
]

# ═══════════════════════════════════════════════════════
#  Field Mask（コスト最小化）
# ═══════════════════════════════════════════════════════
FIELD_MASK = ",".join([
    "places.id",              # 重複排除に使用
    "places.displayName",
    "places.rating",
    "places.userRatingCount",
    "places.formattedAddress",
    "places.websiteUri",
    "nextPageToken",
])

TEXT_URL = "https://places.googleapis.com/v1/places:searchText"


# ═══════════════════════════════════════════════════════
#  Places API
# ═══════════════════════════════════════════════════════
def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

def _center(loc: dict) -> dict:
    return {"latitude": loc["latitude"], "longitude": loc["longitude"]}

def _search_text(loc: dict, text_query: str, page_token=None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount,places.formattedAddress,places.websiteUri",
    }
    payload = {
        "textQuery": text_query,
        "locationBias": {
            "circle": {
                "center": {"latitude": loc["latitude"], "longitude": loc["longitude"]},
                "radius": float(loc["radius_m"]),
            }
        },
    }
    if page_token:
        payload["pageToken"] = page_token
    resp = requests.post(TEXT_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_all(loc: dict, biz: dict) -> list:
    all_places, next_token = [], None
    while True:
        data = _search_text(loc, biz["text_query"], next_token)
        all_places.extend(data.get("places", []))
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(2)
    return all_places

def filter_places(places: list) -> list:
    return [
        p for p in places
        if not p.get("websiteUri") and p.get("userRatingCount", 0) >= MIN_REVIEW_COUNT
    ]


# ═══════════════════════════════════════════════════════
#  URL 生成
# ═══════════════════════════════════════════════════════
def instagram_url(name: str) -> str:
    return f"https://www.instagram.com/explore/search/keyword/?q={urllib.parse.quote(name)}"

def mail_url(name: str) -> str:
    subject = urllib.parse.quote(f"{name} / Website Design Proposal")
    body = urllib.parse.quote(
        f"Hi,\n\nI came across {name} and noticed your business doesn't currently have a website.\n\n"
        "I'd love to help you build a professional website to:\n"
        "  • Attract more customers via Google Search\n"
        "  • Mobile-friendly design\n"
        "  • Google Maps integration\n\n"
        "Would you be open to a quick chat?\n\nBest regards,"
    )
    return f"mailto:?subject={subject}&body={body}"

def mail_url_ja(name: str) -> str:
    subject = urllib.parse.quote(f"{name}様 ／ ホームページ制作のご提案")
    body = urllib.parse.quote(
        f"はじめまして。\n\n{name}様のお店を拝見し、ご連絡いたしました。\n\n"
        "現在、貴店のホームページが見当たらなかったため、\n"
        "集客強化のためのWebサイト制作をご提案できればと思いご連絡しました。\n\n"
        "・スマートフォン対応のデザイン\n"
        "・Googleマップとの連携\n"
        "・SEO対策\n\n"
        "ご興味がございましたら、ぜひ一度お話しさせてください。\n\n"
        "よろしくお願いいたします。"
    )
    return f"mailto:?subject={subject}&body={body}"


# ═══════════════════════════════════════════════════════
#  HTML 生成
# ═══════════════════════════════════════════════════════
CATEGORY_COLORS = {
    # 日本語
    "カフェ":       "bg-amber-100 text-amber-800",
    "歯科医院":     "bg-blue-100 text-blue-800",
    "接骨院・整体": "bg-green-100 text-green-800",
    "ピアノ教室":   "bg-purple-100 text-purple-800",
    "工務店":       "bg-orange-100 text-orange-800",
    "ペットサロン": "bg-pink-100 text-pink-800",
    "動物病院":     "bg-teal-100 text-teal-800",
    # English
    "Cafe":         "bg-amber-100 text-amber-800",
    "Dentist":      "bg-blue-100 text-blue-800",
    "Chiropractor": "bg-green-100 text-green-800",
    "Music School": "bg-purple-100 text-purple-800",
    "Builder":      "bg-orange-100 text-orange-800",
    "Pet Grooming": "bg-pink-100 text-pink-800",
    "Vet":          "bg-teal-100 text-teal-800",
}

LOCATION_COLORS = {
    "Melbourne": "bg-sky-100 text-sky-800",
    "広島":      "bg-rose-100 text-rose-800",
}

def build_places_json(all_results: list) -> str:
    records = []
    for item in all_results:
        loc_name = item["location"]
        label    = item["label"]
        is_ja    = item.get("is_ja", False)
        for p in item["places"]:
            name     = p.get("displayName", {}).get("text", "")
            place_id = p.get("id", "")
            records.append({
                "id":           place_id,   # Google Place ID（安定した一意キー）
                "name":         name,
                "location":     loc_name,
                "category":     label,
                "rating":       p.get("rating", ""),
                "reviewCount":  p.get("userRatingCount", ""),
                "address":      p.get("formattedAddress", ""),
                "instagramUrl": instagram_url(name),
                "mailUrl":      mail_url_ja(name) if is_ja else mail_url(name),
            })
    return json.dumps(records, ensure_ascii=False)

def generate_html(all_results: list, generated_at: str) -> str:
    places_json   = build_places_json(all_results)
    total         = len(json.loads(places_json))   # 重複除去済みの実件数
    locations     = list(dict.fromkeys(r["location"] for r in all_results if r["places"]))
    categories    = list(dict.fromkeys(r["label"]    for r in all_results if r["places"]))

    def tab_buttons(items, filter_fn, extra_class=""):
        return "\n".join(
            f'<button onclick="{filter_fn}(\'{c}\')" data-val="{c}" '
            f'class="filter-btn {extra_class} px-3 py-1.5 rounded-full text-sm font-medium '
            f'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 transition">{c}</button>'
            for c in items
        )

    loc_tabs = tab_buttons(locations, "setLocation", "loc-btn")
    cat_tabs = tab_buttons(categories, "setCategory", "cat-btn")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>営業リスト</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .filter-btn.active {{ background:#1d4ed8; color:#fff; border-color:#1d4ed8; }}
  </style>
</head>
<body class="bg-gray-50 min-h-screen">

  <!-- ヘッダー -->
  <div class="bg-gradient-to-r from-blue-700 to-indigo-700 text-white px-4 py-6 shadow">
    <div class="max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold tracking-tight">🎯 営業リスト</h1>
      <p class="text-blue-200 text-sm mt-1">サイトなし店舗 ／ 生成日: {generated_at}</p>
      <div class="mt-3 flex flex-wrap gap-3 text-sm">
        <span class="bg-white/20 rounded-full px-3 py-1">全 <strong>{total}</strong> 件</span>
        <span class="bg-white/20 rounded-full px-3 py-1">表示中 <strong id="visibleCount">{total}</strong> 件</span>
        <button onclick="restoreAll()"
          class="bg-white/20 hover:bg-white/30 rounded-full px-3 py-1 transition text-xs">
          🔄 削除済みを復元
        </button>
      </div>
    </div>
  </div>

  <!-- フィルター -->
  <div class="max-w-5xl mx-auto px-4 pt-4 space-y-2">
    <!-- エリア -->
    <div class="flex flex-wrap gap-2 items-center">
      <span class="text-xs text-gray-400 font-semibold w-10">エリア</span>
      <button onclick="setLocation('all')" data-val="all"
        class="filter-btn loc-btn active px-3 py-1.5 rounded-full text-sm font-medium border transition">
        すべて
      </button>
      {loc_tabs}
    </div>
    <!-- 業種 -->
    <div class="flex flex-wrap gap-2 items-center pb-2">
      <span class="text-xs text-gray-400 font-semibold w-10">業種</span>
      <button onclick="setCategory('all')" data-val="all"
        class="filter-btn cat-btn active px-3 py-1.5 rounded-full text-sm font-medium border transition">
        すべて
      </button>
      {cat_tabs}
    </div>
  </div>

  <!-- カードグリッド -->
  <div id="cardGrid"
    class="max-w-5xl mx-auto px-4 py-4 pb-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  </div>

  <script>
  const PLACES = {places_json};
  const DELETED_KEY = "sales_list_deleted_v2";
  let currentLocation = "all";
  let currentCategory = "all";

  const CAT_COLORS = {json.dumps(CATEGORY_COLORS, ensure_ascii=False)};
  const LOC_COLORS = {json.dumps(LOCATION_COLORS, ensure_ascii=False)};

  function getDeleted() {{ return new Set(JSON.parse(localStorage.getItem(DELETED_KEY) || "[]")); }}
  function saveDeleted(s) {{ localStorage.setItem(DELETED_KEY, JSON.stringify([...s])); }}

  function renderCard(p) {{
    const catColor = CAT_COLORS[p.category] || "bg-gray-100 text-gray-700";
    const locColor = LOC_COLORS[p.location]  || "bg-slate-100 text-slate-700";
    const stars = p.rating
      ? `<span class="text-yellow-400">${{"★".repeat(Math.round(p.rating))}}</span>
         <span class="font-semibold text-gray-700 ml-1">${{p.rating}}</span>`
      : `<span class="text-gray-400 text-xs">No rating</span>`;
    const reviews = p.reviewCount ? `<span class="text-gray-400 text-xs ml-2">(${{p.reviewCount}})</span>` : "";

    return `
      <div id="card-${{p.id}}" data-loc="${{p.location}}" data-cat="${{p.category}}"
        class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex flex-col gap-3">
        <div class="flex items-start justify-between gap-2">
          <div class="flex flex-wrap gap-1">
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${{locColor}}">${{p.location}}</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${{catColor}}">${{p.category}}</span>
          </div>
          <button onclick="deleteCard('${{p.id}}')"
            class="text-gray-300 hover:text-red-400 text-xl leading-none font-bold shrink-0"
            title="削除">×</button>
        </div>

        <div>
          <h2 class="text-base font-bold text-gray-900 leading-snug">${{p.name}}</h2>
          <div class="flex items-center mt-1">${{stars}}${{reviews}}</div>
        </div>

        <p class="text-gray-500 text-xs leading-relaxed">📍 ${{p.address || "—"}}</p>

        <div class="flex gap-2 pt-1 mt-auto">
          <a href="${{p.instagramUrl}}" target="_blank"
            class="flex-1 text-center text-sm font-medium bg-gradient-to-r from-pink-500 to-purple-500
                   text-white rounded-xl py-2 hover:opacity-90 transition">
            📸 Instagram
          </a>
          <a href="${{p.mailUrl}}"
            class="flex-1 text-center text-sm font-medium bg-blue-600 text-white
                   rounded-xl py-2 hover:bg-blue-700 transition">
            ✉ Mail
          </a>
        </div>
      </div>`;
  }}

  function render() {{
    const deleted = getDeleted();
    const grid = document.getElementById("cardGrid");
    grid.innerHTML = "";
    let visible = 0;
    PLACES.forEach(p => {{
      if (deleted.has(p.id)) return;
      if (currentLocation !== "all" && p.location !== currentLocation) return;
      if (currentCategory !== "all" && p.category !== currentCategory) return;
      grid.insertAdjacentHTML("beforeend", renderCard(p));
      visible++;
    }});
    document.getElementById("visibleCount").textContent = visible;
    if (visible === 0) {{
      grid.innerHTML = `<div class="col-span-3 text-center py-20 text-gray-400 text-sm">該当する店舗がありません</div>`;
    }}
  }}

  function deleteCard(id) {{
    const d = getDeleted(); d.add(id); saveDeleted(d); render();
  }}
  function restoreAll() {{ localStorage.removeItem(DELETED_KEY); render(); }}

  function setLocation(val) {{
    currentLocation = val;
    document.querySelectorAll(".loc-btn").forEach(b => b.classList.toggle("active", b.dataset.val === val));
    render();
  }}
  function setCategory(val) {{
    currentCategory = val;
    document.querySelectorAll(".cat-btn").forEach(b => b.classList.toggle("active", b.dataset.val === val));
    render();
  }}

  render();
  </script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════
#  メイン
# ═══════════════════════════════════════════════════════
def main():
    total_api_calls = sum(len(loc["business_types"]) for loc in SEARCH_LOCATIONS)
    print(f"=== 営業リスト生成 ===")
    print(f"エリア数: {len(SEARCH_LOCATIONS)}  予定APIコール数: {total_api_calls}+\n")

    all_results = []
    call_count  = 0
    seen_ids    = set()   # エリア・業種をまたいだ全体重複排除用

    for loc in SEARCH_LOCATIONS:
        print(f"\n📍 {loc['name']} (半径 {loc['radius_m']}m)")
        is_ja = loc["business_types"] is BUSINESS_TYPES_JA

        for biz in loc["business_types"]:
            call_count += 1
            label = biz["label"]
            print(f"  [{call_count}/{total_api_calls}] {label} ...", end=" ", flush=True)
            try:
                places   = fetch_all(loc, biz)
                filtered = filter_places(places)

                # place_id で重複除去（同業種の別クエリ・別エリアの混入を防ぐ）
                unique = []
                for p in filtered:
                    pid = p.get("id", "")
                    if pid not in seen_ids:
                        seen_ids.add(pid)
                        unique.append(p)

                print(f"{len(places)}件取得 → フィルター{len(filtered)}件 → 重複除去後{len(unique)}件")
                all_results.append({
                    "location": loc["name"],
                    "label":    label,
                    "places":   unique,
                    "is_ja":    is_ja,
                })
            except requests.HTTPError as e:
                print(f"ERROR {e.response.status_code}: {e.response.text[:120]}")
                all_results.append({"location": loc["name"], "label": label, "places": [], "is_ja": is_ja})
            time.sleep(1)

    total = sum(len(r["places"]) for r in all_results)
    print(f"\n合計: {total} 件 → {OUTPUT_FILE} 生成中...")

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = generate_html(all_results, generated_at)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ {OUTPUT_FILE} 保存完了 ({len(html):,} bytes)")
    print(f"Vercel: cd cafe-search && vercel --yes")


if __name__ == "__main__":
    main()
