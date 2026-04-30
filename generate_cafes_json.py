"""
places_db.json を読み込み、カフェ情報を cafe-website/lib/cafes.json に書き出す。

対象カテゴリ: Cafe / カフェ
既存の cafes.json は上書きされる。
slug 重複は自動採番で回避。
"""

import json
import re
import unicodedata
import urllib.parse
from pathlib import Path

PLACES_DB   = Path(__file__).parent / "places_db.json"
OUTPUT_JSON = Path(__file__).parent.parent / "cafe-website" / "lib" / "cafes.json"
DEMO_BASE   = "https://cafe-model.vercel.app"

CAFE_CATEGORIES = {"Cafe", "カフェ"}

HERO_IMAGES = [
    "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1600&q=80",
    "https://images.unsplash.com/photo-1559925393-8be0ec4767c8?w=1600&q=80",
    "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=1600&q=80",
    "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=1600&q=80",
    "https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=1600&q=80",
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=1600&q=80",
    "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=1600&q=80",
]

INTERIOR_IMAGES = [
    "https://images.unsplash.com/photo-1445116572660-236099ec97a0?w=800&q=80",
    "https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=800&q=80",
    "https://images.unsplash.com/photo-1600093463592-8e36ae95ef56?w=800&q=80",
    "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=800&q=80",
    "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80",
]


def slugify(name: str) -> str:
    """カフェ名 → URL スラッグ (例: "Café Felice" → "cafe-felice")"""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def parse_address(full: str) -> dict:
    parts = [p.strip() for p in full.split(",")]
    return {
        "line1": parts[0] if parts else "",
        "line2": parts[1] if len(parts) > 1 else "",
        "city":  ", ".join(parts[2:]) if len(parts) > 2 else "",
        "hint":  "",
    }


def make_entry(place: dict, idx: int) -> dict:
    name    = place["name"]
    is_ja   = place.get("location", "") == "広島"
    address = parse_address(place.get("address", ""))
    rating  = float(place.get("rating") or 4.0)
    reviews = place.get("reviewCount", 0)
    location = place.get("location", "")

    if is_ja:
        menu = [
            {"title": "コーヒー", "icon": "☕", "items": [
                {"name": "エスプレッソ",     "desc": "シングルオリジン",          "price": "¥500"},
                {"name": "フラットホワイト", "desc": "なめらかなマイクロフォーム", "price": "¥600"},
                {"name": "アイスコーヒー",   "desc": "12時間コールドブリュー",    "price": "¥650"},
                {"name": "オーツラテ",       "desc": "植物性ミルク使用",           "price": "¥700"},
            ]},
            {"title": "フード", "icon": "🥐", "items": [
                {"name": "クロワッサン",   "desc": "毎朝焼き立て",             "price": "¥400"},
                {"name": "バタートースト", "desc": "厚切りトーストにバター",   "price": "¥500"},
                {"name": "スコーン",       "desc": "クリームとジャム添え",     "price": "¥450"},
                {"name": "本日のケーキ",   "desc": "スタッフにお尋ねください", "price": "¥600"},
            ]},
        ]
        hours = [
            {"days": "月曜〜金曜", "time": "8:00 am – 5:00 pm"},
            {"days": "土・日曜",   "time": "9:00 am – 4:00 pm"},
        ]
        tagline    = "地元に愛される、こだわりのコーヒーと居心地のいい空間。"
        menu_sub   = "季節の食材とスペシャルティコーヒーで、毎日を少し豊かに。"
        menu_note  = "メニューは季節により変更されます。スタッフにお尋ねください。"
        reviews_arr = [{"author": "Googleレビュー",
                         "text": f"地元で人気のカフェ。{reviews}件以上のレビューが集まる実力店。コーヒーが絶品でスタッフも親切です。",
                         "rating": min(5, round(rating))}]
    else:
        menu = [
            {"title": "Coffee", "icon": "☕", "items": [
                {"name": "Espresso",   "desc": "Single origin, bright & clean",    "price": "$4.5"},
                {"name": "Flat White", "desc": "Velvety microfoam, full-bodied",   "price": "$5.5"},
                {"name": "Oat Latte",  "desc": "Creamy, naturally sweet",          "price": "$6.5"},
                {"name": "Cold Brew",  "desc": "12-hour steep, smooth & dark",     "price": "$7"},
            ]},
            {"title": "Bites", "icon": "🥐", "items": [
                {"name": "Croissant",     "desc": "Freshly baked daily",              "price": "$5"},
                {"name": "Avocado Toast", "desc": "Smashed avo on sourdough",         "price": "$16"},
                {"name": "Banana Bread",  "desc": "House-made, with whipped butter",  "price": "$6"},
                {"name": "Seasonal Tart", "desc": "Ask your barista today",           "price": "$12"},
            ]},
        ]
        hours = [
            {"days": "Monday – Friday",   "time": "7:00 am – 4:00 pm"},
            {"days": "Saturday – Sunday", "time": "8:00 am – 3:00 pm"},
        ]
        tagline    = "Great coffee, warm vibes — your new favourite local."
        menu_sub   = "Seasonal ingredients and specialty coffee, served with care every day."
        menu_note  = "Menu changes seasonally. Dietary options available — ask your barista."
        reviews_arr = [{"author": "Google Review",
                         "text": f"A fantastic local with {reviews}+ happy customers. Great coffee and a warm atmosphere.",
                         "rating": min(5, round(rating))}]

    map_embed = (
        f"https://maps.google.com/maps?q={urllib.parse.quote(place.get('address', ''))}&output=embed"
    )

    return {
        "name":          name,
        "tagline":       tagline,
        "eyebrow":       f"{location} · {address['line1']}",
        "menuSubtitle":  menu_sub,
        "address":       address,
        "phone":         "",
        "instagram":     None,
        "rating":        rating,
        "hours":         hours,
        "wineNote":      None,
        "menu":          menu,
        "menuNote":      menu_note,
        "transport":     [],
        "reviews":       reviews_arr,
        "mapEmbed":      map_embed,
        "heroImage":     HERO_IMAGES[idx % len(HERO_IMAGES)],
        "interiorImage": INTERIOR_IMAGES[idx % len(INTERIOR_IMAGES)],
    }


def main() -> None:
    if not PLACES_DB.exists():
        print(f"❌ {PLACES_DB} が見つかりません。multi_search.py を先に実行してください。")
        return

    with open(PLACES_DB, encoding="utf-8") as f:
        db: list[dict] = json.load(f)

    cafes = [p for p in db if p.get("category") in CAFE_CATEGORIES]
    print(f"📂 places_db: {len(db)} 件 → カフェ {len(cafes)} 件を変換\n")

    result: dict = {}
    used: set[str] = set()

    for idx, place in enumerate(cafes):
        slug = slugify(place["name"]) or f"cafe-{idx}"
        base, n = slug, 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        result[slug] = make_entry(place, idx)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(result)} 件 → {OUTPUT_JSON}\n")
    for slug in result:
        print(f"  {DEMO_BASE}/{slug}")


if __name__ == "__main__":
    main()
