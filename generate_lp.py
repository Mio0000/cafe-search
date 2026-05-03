#!/usr/bin/env python3
"""
LP generator: lib/services.json → dist/{category}-{slug}.html
Usage:
  python3 generate_lp.py                              # all pages
  python3 generate_lp.py --id ChIJ...                 # 1件だけ再生成
  python3 generate_lp.py --deploy                     # 生成後 Vercel へデプロイ
  GOOGLE_MAPS_API_KEY=AIza... python3 generate_lp.py  # APIで電話番号・評価を取得
"""
import json
import os
import random
import re
import subprocess
import sys
import unicodedata
from datetime import date

from jinja2 import Environment, FileSystemLoader

try:
    import requests as _req
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

SERVICES_JSON  = "lib/services.json"
TEMPLATE_DIR   = "templates"
OUTPUT_DIR     = "dist"
GOOGLE_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# ─── Hero images: 5 per category (Unsplash CDN) ──────────────────────────────
HERO_IMAGES = {
    "Plumber": [
        "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1562664377-709f2c337eb2?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1574937612330-ac3c0e9e79f7?w=1920&q=80&auto=format",
    ],
    "Electrician": [
        "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1509390836518-dc36f66a6859?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1558449028-b53a39d100fc?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1569516449771-41c89ee14ca3?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1593068931940-a46b1cf14d85?w=1920&q=80&auto=format",
    ],
    "Roofing": [
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1565364887179-c6307b1f4e26?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1629734440153-ea3e8ddb7eb1?w=1920&q=80&auto=format",
    ],
    "HVAC": [
        "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1583521214690-73421a1829a9?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920&q=80&auto=format",
    ],
    "Landscaping": [
        "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1558904541-efa843a96f01?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1472396961693-142e6e269027?w=1920&q=80&auto=format",
    ],
    "Pest Control": [
        "https://images.unsplash.com/photo-1564069114553-7215e1ff1890?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1590496793929-36417d3117de?w=1920&q=80&auto=format",
        "https://images.unsplash.com/photo-1600880292089-90a7e086ee0c?w=1920&q=80&auto=format",
    ],
}

# ─── SVG icon paths (inner content only; wrap in template) ───────────────────
# ViewBox: 0 0 24 24, fill:none, stroke:currentColor, stroke-width:1.8,
# stroke-linecap:round, stroke-linejoin:round

_I = {
    # ── Services ─────────────────────────────────────────────────────────────
    "drain":    '<circle cx="12" cy="12" r="8"/><path d="M12 4v16M4 12h16"/>'
                '<path d="M6.34 6.34l11.32 11.32M17.66 6.34 6.34 17.66"/>',
    "pipe":     '<path d="M3 8h18M3 16h18"/>'
                '<path d="M3 8Q3 4 7 4h10q4 0 4 4M3 16q0 4 4 4h10q4 0 4-4"/>',
    "hotwater": '<path d="M12 2C12 2 5 9.5 5 14a7 7 0 0 0 14 0C19 9.5 12 2 12 2z"/>'
                '<path d="M9 14c0-1.66 1.34-3 3-3s3 1.34 3 3"/>',
    "faucet":   '<path d="M5 12h6M14 8h3a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-3"/>'
                '<path d="M8 8v8M5 8h6M5 16h6"/><circle cx="5" cy="12" r="1"/>',
    "bolt":     '<path d="M13 2 6 13h6l-1 9 9-11h-6l1-9z"/>',
    "bulb":     '<path d="M9 18h6M10 22h4"/>'
                '<path d="M12 2a7 7 0 0 1 5.2 11.8L16 16H8l-1.2-2.2A7 7 0 0 1 12 2z"/>',
    "plug":     '<path d="M12 22v-5"/><path d="M9 7V4M15 7V4"/>'
                '<rect x="5" y="7" width="14" height="7" rx="2"/>'
                '<path d="M8 14v3h8v-3"/>',
    "shield_check": '<path d="M12 2L4 6v6c0 5.25 3.5 10.16 8 11.36C16.5 22.16 20 17.25 20 12V6l-8-4z"/>'
                    '<path d="M9 12l2 2 4-4"/>',
    "roof":     '<path d="M3 12 12 3l9 9"/><path d="M5 12v8h14v-8"/>'
                '<path d="M9 20v-5h6v5"/>',
    "gutter":   '<path d="M4 8h16v6H4z"/><path d="M8 14v4M16 14v4"/>'
                '<path d="M6 18h12"/>',
    "reroofing":'<path d="M3 12 12 3l9 9"/><path d="M5 12v8h14v-8"/>'
                '<path d="M14 7l3 3-6 6-3-3z"/><path d="M19 5l-3 3"/>',
    "inspect":  '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>',
    "snowflake":'<line x1="12" y1="2" x2="12" y2="22"/>'
                '<line x1="2" y1="8" x2="22" y2="16"/>'
                '<line x1="2" y1="16" x2="22" y2="8"/>'
                '<circle cx="12" cy="6" r="1.5"/><circle cx="12" cy="18" r="1.5"/>',
    "thermo":   '<path d="M12 2a3 3 0 0 0-3 3v8.26A6 6 0 1 0 15 13.26V5a3 3 0 0 0-3-3z"/>'
                '<circle cx="12" cy="18" r="2"/>'
                '<path d="M9 8h2M9 11h2"/>',
    "wrench":   '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3-3a6 6 0 0 1-7.8 7.8L6 19.6a2 2 0 0 1-2.8-2.8l5.5-5.9a6 6 0 0 1 7.8-7.8l-3 3z"/>',
    "clipboard":'<rect x="8" y="2" width="8" height="4" rx="1"/>'
                '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
                '<path d="M9 12h6M9 16h4"/>',
    "scissors": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>'
                '<path d="M20 4 8.12 15.88M14.47 14.48 20 20M8.12 8.12 12 12"/>',
    "leaf":     '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8a7 7 0 0 1-9 6.79 7 7 0 0 1-2.19-3.32"/>',
    "droplet":  '<path d="M12 2C12 2 5 9.5 5 14a7 7 0 0 0 14 0C19 9.5 12 2 12 2z"/>',
    "tree":     '<circle cx="12" cy="7" r="4"/><path d="M12 14a6 6 0 0 1 6 6H6a6 6 0 0 1 6-6z"/>'
                '<path d="M12 11v3"/>',
    "bug":      '<path d="M8 2c0 2-2 4-2 6"/><path d="M16 2c0 2 2 4 2 6"/>'
                '<circle cx="12" cy="11" r="4"/>'
                '<path d="M5 8 2 10M19 8l3 2M2 16l3-2M22 16l-3-2"/>'
                '<path d="M10 18a4 4 0 0 0 4 4 4 4 0 0 0 4-4"/>',
    "termite":  '<path d="M3 12 12 3l9 9"/><path d="M5 12v7h14v-7"/>'
                '<circle cx="15" cy="13" r="3"/><path d="M17.5 15.5 20 18"/>',
    "rodent":   '<ellipse cx="10" cy="12" rx="6" ry="5"/>'
                '<path d="M16 11c2-1 4 0 4 2"/>'
                '<path d="M7 7C7 5 9 4 10 4 11 4 12 5 12 6"/>'
                '<path d="M8 17c0 2 4 3 6 2"/>',
    "barrier":  '<rect x="2" y="10" width="20" height="4" rx="2"/>'
                '<path d="M7 10V7M12 10V7M17 10V7"/>'
                '<path d="M7 14v3M12 14v3M17 14v3"/>',
    # ── Nav logo icons (22x22 viewbox) ────────────────────────────────────────
    "nav_plumber":    '<path d="M14 3a3 3 0 0 1 3 3 3 3 0 0 1-3 3L5 18a2 2 0 0 1-3-3L11 6a3 3 0 0 1 3-3z"/>',
    "nav_electrician":'<path d="M11 2 5 13h6l-1 9 9-12h-6l1-8z"/>',
    "nav_roofing":    '<path d="M2 11 11 3l9 8"/><path d="M4 11v9h14v-9"/><path d="M8 20v-4h6v4"/>',
    "nav_hvac":       '<line x1="11" y1="2" x2="11" y2="20"/>'
                      '<line x1="2" y1="7.5" x2="20" y2="14.5"/>'
                      '<line x1="2" y1="14.5" x2="20" y2="7.5"/>',
    "nav_landscaping":'<path d="M10 18A7 7 0 0 1 8.8 5C14.5 4 16 3.5 18 1c1 2 2 4.18 2 8a7 7 0 0 1-9 6.79"/>'
                      '<path d="M10 18v3M7 21h6"/>',
    "nav_pest":       '<path d="M11 2 3 6v6c0 5.25 3.5 10.16 8 11.36C15.5 22.16 19 17.25 19 12V6l-8-4z"/>'
                      '<path d="M8 12l2 2 4-4"/>',
}

# ─── Shared pillar definitions ────────────────────────────────────────────────
_PILLARS = [
    {
        "icon": '<path d="M11 2 3 6v6c0 5.25 3.5 10.16 8 11.36C15.5 22.16 19 17.25 19 12V6l-8-4z"/><path d="M8 12l2 2 4-4"/>',
        "title": "Honest & Transparent",
        "text":  "No hidden costs, no upselling. We tell you exactly what's needed and why.",
    },
    {
        "icon": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 3"/>',
        "title": "Fast & Punctual",
        "text":  "We respond quickly and arrive when we say we will. Your time matters.",
    },
    {
        "icon": '<path d="M8 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/>',
        "title": "Quality Workmanship",
        "text":  "Every job completed to a standard we're proud of. No shortcuts, ever.",
    },
    {
        "icon": '<path d="M3 11 12 3l9 8"/><path d="M5 11v9h14v-9"/><circle cx="12" cy="15" r="2"/>',
        "title": "Locally Based",
        "text":  "We know the area, conditions, and local requirements. Better results.",
    },
]

# ─── Category data ────────────────────────────────────────────────────────────
CATEGORY_DATA = {
    "Plumber": {
        "tagline":       "Expert plumbing solutions for homes and businesses in {suburb}",
        "nav_icon":      _I["nav_plumber"],
        "category_label":"Licensed Plumber",
        "trust_items": [
            "Same-day emergency response available",
            "Fully licensed and insured plumbers",
            "Upfront pricing — no hidden costs",
        ],
        "services": [
            {"name": "Blocked Drains",       "desc": "Fast diagnosis and clearing of all drain types using professional equipment.", "svg": _I["drain"]},
            {"name": "Pipe Repairs & Leaks", "desc": "Burst pipes, slow leaks and full repiping with quality materials.", "svg": _I["pipe"]},
            {"name": "Hot Water Systems",    "desc": "Installation and repair of all brands — gas, electric and solar.", "svg": _I["hotwater"]},
            {"name": "Bathroom & Kitchen",   "desc": "Renovations, fixtures and new installations to the highest standard.", "svg": _I["faucet"]},
        ],
        "emergency": True,
        "license_text":  "Licensed Plumber",
        "reviews": [
            {"headline": "Solved a Crisis at 7pm", "text": "Called at 7pm with a burst pipe and they were here within the hour. Fixed everything cleanly with no mess. Highly recommend.", "author": "Sarah M.", "initial": "S"},
            {"headline": "Professional & Fair",    "text": "Professional, punctual and very fairly priced. Explained everything before starting. Will definitely use again.", "author": "James K.", "initial": "J"},
            {"headline": "Reliable Every Time",    "text": "Quick response, honest advice and quality work. Found the issue others had missed. Couldn't be happier.", "author": "Anna P.", "initial": "A"},
            {"headline": "Worth Every Cent",       "text": "Very knowledgeable and explained every step. No surprises on the bill. Absolutely brilliant.", "author": "Michael C.", "initial": "M"},
        ],
        "about_tagline": "We fix plumbing problems properly — no shortcuts, no surprises. When you call, we arrive on time, diagnose the real issue, and sort it right the first time.",
    },
    "Electrician": {
        "tagline":       "Safe, reliable electrical solutions for {suburb} homes and businesses",
        "nav_icon":      _I["nav_electrician"],
        "category_label":"A-Grade Electrician",
        "trust_items": [
            "A-Grade licensed and fully insured",
            "Same-day service for urgent electrical faults",
            "Transparent quoting — no surprise bills",
        ],
        "services": [
            {"name": "Switchboard Upgrades", "desc": "Safety switches and circuit breaker upgrades for full compliance.", "svg": _I["bolt"]},
            {"name": "LED Lighting",          "desc": "Energy-efficient lighting design, supply and professional installation.", "svg": _I["bulb"]},
            {"name": "Power Points & USB",    "desc": "Additional points installed anywhere in your home or business.", "svg": _I["plug"]},
            {"name": "Safety Inspections",    "desc": "Compliance reports and hazard assessments with full documentation.", "svg": _I["shield_check"]},
        ],
        "emergency": True,
        "license_text":  "A-Grade Licensed Electrician",
        "reviews": [
            {"headline": "Brilliant LED Upgrade",   "text": "Upgraded our whole switchboard and installed new LED lighting throughout. Neat, fast and no mess. Brilliant.", "author": "Tom W.", "initial": "T"},
            {"headline": "Knowledgeable & Honest",  "text": "Very knowledgeable and took the time to explain the safety issues. Competitive pricing. Highly recommended.", "author": "Linda R.", "initial": "L"},
            {"headline": "Fixed What Others Missed","text": "Diagnosed a fault three other electricians had overlooked. Fixed quickly and fairly priced. Excellent.", "author": "David S.", "initial": "D"},
            {"headline": "On Time, Every Time",     "text": "Arrived exactly when they said, explained clearly and left no mess. Professional service from start to finish.", "author": "Emma W.", "initial": "E"},
        ],
        "about_tagline": "We deliver safe, lasting electrical work — every time. Our A-Grade licence means your property is in qualified hands, and our straight-talking advice means no nasty surprises.",
    },
    "Roofing": {
        "tagline":       "Professional roofing repairs and restoration in {suburb}",
        "nav_icon":      _I["nav_roofing"],
        "category_label":"Licensed Roofing Contractor",
        "trust_items": [
            "Licensed and fully insured roofing specialists",
            "Storm damage and insurance claims supported",
            "Free detailed roof inspection and report",
        ],
        "services": [
            {"name": "Roof Repairs",        "desc": "Leak detection, broken tiles and storm damage — fixed to last.", "svg": _I["roof"]},
            {"name": "Gutters & Downpipes", "desc": "Cleaning, repairs and full replacement with quality materials.", "svg": _I["gutter"]},
            {"name": "Re-Roofing",          "desc": "Full replacement with premium materials and a workmanship guarantee.", "svg": _I["reroofing"]},
            {"name": "Roof Inspections",    "desc": "Detailed condition reports and maintenance plans with photos.", "svg": _I["inspect"]},
        ],
        "emergency": True,
        "license_text":  "Licensed Roofing Contractor",
        "reviews": [
            {"headline": "Found What Others Missed","text": "Fixed a major leak before storm season. They found two other problem areas and sorted them all at a great price.", "author": "Michael B.", "initial": "M"},
            {"headline": "Honest & No Upselling",   "text": "Came for a free inspection and gave honest advice with no upselling. Straightforward and professional.", "author": "Carol T.", "initial": "C"},
            {"headline": "Quick & Thorough",        "text": "Arrived the next day after my call and had the job done by afternoon. Clean, tidy and affordable.", "author": "Peter H.", "initial": "P"},
            {"headline": "Excellent Storm Repairs", "text": "Handled the insurance claim and repairs seamlessly. Highly professional from quote to completion.", "author": "Jenny L.", "initial": "J"},
        ],
        "about_tagline": "We don't just patch roofs — we find the root cause and fix it properly. Our team brings honesty, care, and craftsmanship to every job in {suburb}.",
    },
    "HVAC": {
        "tagline":       "Heating and cooling specialists for {suburb} homes and businesses",
        "nav_icon":      _I["nav_hvac"],
        "category_label":"Refrigeration & A/C Licence",
        "trust_items": [
            "All major brands supplied, installed and serviced",
            "Fully licensed refrigeration mechanics",
            "Upfront quotes with no obligation",
        ],
        "services": [
            {"name": "Split System Installation", "desc": "All major brands supplied and installed by licensed technicians.", "svg": _I["snowflake"]},
            {"name": "Ducted Systems",            "desc": "Full ducted heating and cooling design, supply and installation.", "svg": _I["thermo"]},
            {"name": "Servicing & Repairs",       "desc": "All brands repaired and maintained to manufacturer specs.", "svg": _I["wrench"]},
            {"name": "Annual Maintenance",        "desc": "Service plans to keep your system running at peak efficiency.", "svg": _I["clipboard"]},
        ],
        "emergency": False,
        "license_text":  "Refrigeration & A/C Licence",
        "reviews": [
            {"headline": "Ducted System Perfection","text": "Installed a new ducted system in our home. Team was tidy, efficient and finished ahead of schedule.", "author": "David L.", "initial": "D"},
            {"headline": "Same-Day Fix",            "text": "AC wasn't cooling properly. Diagnosed and fixed same day for a very reasonable price. Great service.", "author": "Karen S.", "initial": "K"},
            {"headline": "Great Value & Service",   "text": "Installed two split systems quickly and cleanly. Very professional and great value. Highly recommended.", "author": "Mark R.", "initial": "M"},
            {"headline": "Reliable Maintenance",    "text": "Annual service is always thorough and on time. System runs perfectly year-round thanks to this team.", "author": "Sue N.", "initial": "S"},
        ],
        "about_tagline": "Your comfort is our priority. We install, service and repair all brands with precision and care — delivering year-round comfort to homes and businesses in {suburb}.",
    },
    "Landscaping": {
        "tagline":       "Transforming outdoor spaces across {suburb} and surrounds",
        "nav_icon":      _I["nav_landscaping"],
        "category_label":"Professional Landscaper",
        "trust_items": [
            "Reliable, regular service you can count on",
            "Custom designs tailored to your property",
            "Free consultation and competitive pricing",
        ],
        "services": [
            {"name": "Lawn Mowing & Edging",    "desc": "Regular mowing, edging and lawn care programs to keep your lawn pristine.", "svg": _I["scissors"]},
            {"name": "Garden Design & Planting","desc": "Custom layouts and seasonal planting for stunning year-round colour.", "svg": _I["leaf"]},
            {"name": "Irrigation Systems",      "desc": "Automated watering solutions designed for all garden sizes.", "svg": _I["droplet"]},
            {"name": "Tree & Hedge Trimming",   "desc": "Professional pruning, shaping and removal by trained specialists.", "svg": _I["tree"]},
        ],
        "emergency": False,
        "license_text":  "Professional Landscaper",
        "reviews": [
            {"headline": "Transformed Our Backyard", "text": "Transformed our overgrown backyard into something we're genuinely proud of. Great communication and reasonable rates.", "author": "Emma P.", "initial": "E"},
            {"headline": "Always On Time",           "text": "Weekly mowing and quarterly maintenance. Always on time, always thorough. Best landscaper we've used.", "author": "Robert H.", "initial": "R"},
            {"headline": "Beautiful Garden Design",  "text": "Designed and planted our entire front garden. The result is stunning — exactly what we envisioned.", "author": "Claire M.", "initial": "C"},
            {"headline": "Great Attention to Detail","text": "Meticulous work, great communication throughout. Everything looks better than it ever did.", "author": "Tom B.", "initial": "T"},
        ],
        "about_tagline": "We bring outdoor spaces to life. From weekly lawn care to full garden transformations, every job is handled with care and attention to detail in {suburb}.",
    },
    "Pest Control": {
        "tagline":       "Protecting {suburb} homes and businesses from pests year-round",
        "nav_icon":      _I["nav_pest"],
        "category_label":"Licensed Pest Controller",
        "trust_items": [
            "Licensed pest controllers with full insurance",
            "Safe, family and pet-friendly treatment options",
            "Thorough inspection and written report provided",
        ],
        "services": [
            {"name": "General Pest Control",    "desc": "Ants, spiders, cockroaches, silverfish and more — fully treated.", "svg": _I["bug"]},
            {"name": "Termite Inspections",     "desc": "Pre-purchase and annual timber pest reports with detailed findings.", "svg": _I["termite"]},
            {"name": "Rodent Control",          "desc": "Mice and rat baiting and proofing programs that get lasting results.", "svg": _I["rodent"]},
            {"name": "Preventative Treatments", "desc": "Regular barrier treatments to keep pests out for good.", "svg": _I["barrier"]},
        ],
        "emergency": False,
        "license_text":  "Licensed Pest Controller",
        "reviews": [
            {"headline": "Caught What Others Missed","text": "Found a termite issue during a routine inspection and treated it quickly with a full management plan. Excellent.", "author": "Greg M.", "initial": "G"},
            {"headline": "Completely Pest-Free Now", "text": "Regular quarterly visits keep our place completely pest-free. Reliable, discreet and thorough.", "author": "Olivia C.", "initial": "O"},
            {"headline": "Fast & Effective",         "text": "Dealt with a significant ant problem. Results were noticeable within days. Highly recommend.", "author": "Chris F.", "initial": "C"},
            {"headline": "Professional & Discreet",  "text": "Turned up on time, caused no disruption and left no trace — except the pests being gone.", "author": "Rachel D.", "initial": "R"},
        ],
        "about_tagline": "We protect homes and businesses from pests year-round using safe, effective treatments. Licensed, thorough, and always discreet in {suburb}.",
    },
}

PLACEHOLDER_PHONE = "1300 XXX XXX"


# ─── Google Maps Places API ───────────────────────────────────────────────────

def fetch_place_details(place_id: str) -> dict | None:
    
    """Return phone, rating, review_count and top 5-star reviews from Places API."""
    if not GOOGLE_API_KEY or not _HAS_REQUESTS or not place_id:
        return None
    if not place_id.startswith("ChIJ"):
        # print(f"  [Skip] Placeholder ID found: {place_id}") # 必要ならコメントアウト解除
        return None
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    try:
        resp = _req.get(url, params={
            "place_id": place_id,
            "fields":   "name,formatted_phone_number,rating,user_ratings_total,reviews",
            "language": "en",
            "key":      GOOGLE_API_KEY,
        }, timeout=10)
        data = resp.json()
    except Exception as exc:
        print(f"  [API] {place_id}: {exc}", file=sys.stderr)
        return None

    if data.get("status") != "OK":
        print(f"  [API] {place_id}: status={data.get('status')}", file=sys.stderr)
        return None

    result = data.get("result", {})
    five_star = [r for r in result.get("reviews", []) if r.get("rating", 0) >= 5]

    reviews = []
    for r in five_star[:6]:
        text = r.get("text", "").strip()
        author = r.get("author_name", "").strip()
        initial = author[0].upper() if author else "G"
        # Derive a short headline from the first few words
        words = text.split()[:5]
        headline = " ".join(words).rstrip(".,!?") if words else "Great Service"
        reviews.append({"headline": headline, "text": text, "author": author, "initial": initial})

    return {
        "phone":        result.get("formatted_phone_number"),
        "rating":       result.get("rating"),
        "review_count": result.get("user_ratings_total"),
        "reviews":      reviews or None,
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def star_string(rating) -> str:
    full = min(5, round(float(rating))) if rating else 5
    return "★" * full + "☆" * (5 - full)


# ─── Context builder ─────────────────────────────────────────────────────────

def build_context(svc: dict, cat: dict, api: dict | None) -> dict:
    suburb = svc.get("suburb", "Melbourne")

    # Merge API data over static defaults
    rating       = (api and api.get("rating")) or svc.get("rating") or 4.8
    review_count = (api and api.get("review_count")) or svc.get("reviewCount") or 0
    phone        = (api and api.get("phone")) or svc.get("phone") or PLACEHOLDER_PHONE
    reviews_raw  = (api and api.get("reviews")) or cat["reviews"]

    # Ensure author suburb substitution for static reviews
    reviews = [
        {**r, "author": r["author"].replace("{suburb}", suburb)}
        for r in reviews_raw
    ]

    # Split reviews across two marquee rows
    mid = max(1, len(reviews) // 2)
    reviews_row1 = reviews[:mid]
    reviews_row2 = reviews[mid:] or reviews[:mid]

    # Ensure minimum 2 cards per row (duplicate if fewer)
    if len(reviews_row1) < 2:
        reviews_row1 = reviews_row1 * 3
    if len(reviews_row2) < 2:
        reviews_row2 = reviews_row2 * 3

    about_tagline = cat.get("about_tagline", cat["tagline"]).replace("{suburb}", suburb)

    return {
        "name":          svc["name"],
        "category":      svc["category"],
        "suburb":        suburb,
        "rating":        rating,
        "review_count":  review_count,
        "stars":         star_string(rating),
        "tagline":       cat["tagline"].replace("{suburb}", suburb),
        "services":      cat["services"],
        "emergency":     cat["emergency"],
        "license_text":  cat["license_text"],
        "reviews_row1":  reviews_row1,
        "reviews_row2":  reviews_row2,
        "hero_image":    random.choice(HERO_IMAGES.get(svc["category"], HERO_IMAGES["Plumber"])),
        "phone":         phone,
        "phone_raw":     re.sub(r"\s+", "", phone),
        "year":          date.today().year,
        "notes":         svc.get("notes", ""),
        "maps_url":      svc.get("googleMapsUrl", ""),
        "nav_icon":      cat["nav_icon"],
        "category_label":cat["category_label"],
        "trust_items":   cat["trust_items"],
        "pillars":       _PILLARS,
        "about_tagline": about_tagline,
        "footer_tagline":f"{suburb}'s trusted local {svc['category'].lower()}. Licensed, insured, and locally owned.",
        "place_id":      svc.get("id", ""),
    }


# ─── Generator ───────────────────────────────────────────────────────────────

def generate_one(svc: dict, template, target_id: str | None = None) -> str | None:
    if target_id and svc.get("id") != target_id:
        return None
    cat_name = svc.get("category", "")
    if cat_name not in CATEGORY_DATA:
        return None
    cat = CATEGORY_DATA[cat_name]

    # Try Google API if key is set
    api = fetch_place_details(svc.get("id", "")) if GOOGLE_API_KEY else None
    if api:
        print(f"  [API] fetched live data for {svc['name']}")

    ctx      = build_context(svc, cat, api)
    filename = f"{slugify(cat_name)}-{slugify(svc['name'])}.html"
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template.render(**ctx))
    return filename


def write_index(entries: list[tuple[str, str]]) -> None:
    rows = "\n".join(
        f'  <li><a href="{fn}">{name}</a></li>'
        for name, fn in entries
    )
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>Generated LPs</title>"
        "<style>body{font-family:sans-serif;padding:2rem;line-height:1.8;}"
        "a{color:#3C938D;}h1{margin-bottom:1rem;}</style></head><body>"
        f"<h1>Generated Landing Pages ({len(entries)})</h1><ul>\n{rows}\n</ul>"
        "</body></html>"
    )
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def deploy_to_vercel() -> None:
    print("\nDeploying to Vercel...")
    result = subprocess.run(
        ["vercel", "--prod", "--yes"],
        capture_output=True,
        text=True,
    )
    # Echo all output so progress is visible
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode == 0:
        # Extract and highlight the production URL
        url = None
        for line in result.stdout.splitlines():
            if "https://" in line and ("Production" in line or ".vercel.app" in line):
                # Pick the https:// token from the line
                for token in line.split():
                    if token.startswith("https://"):
                        url = token.rstrip(".,")
                        break
            if url:
                break
        print(f"\nDeploy complete.")
        if url:
            print(f"Production URL: {url}")
    else:
        print(f"Vercel deploy failed (exit {result.returncode}).", file=sys.stderr)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    args       = sys.argv[1:]
    target_id  = None
    do_deploy  = "--deploy" in args

    if "--id" in args:
        idx       = args.index("--id")
        target_id = args[idx + 1] if idx + 1 < len(args) else None

    if GOOGLE_API_KEY:
        print(f"Google Maps API key found — will fetch live data.\n")
    else:
        print("GOOGLE_MAPS_API_KEY not set — using static data.\n")

    with open(SERVICES_JSON, encoding="utf-8") as f:
        services = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    env      = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("lp.html.j2")

    generated, skipped = [], []

    for svc in services:
        fn = generate_one(svc, template, target_id)
        if fn:
            generated.append((svc["name"], fn))
            print(f"  {fn}")
        elif svc.get("category") not in CATEGORY_DATA:
            skipped.append(svc.get("name", "?"))

    if not target_id:
        write_index(generated)

    print(f"\n{len(generated)} pages generated -> {OUTPUT_DIR}/")
    if skipped:
        print(f"Skipped (unsupported category): {', '.join(skipped)}")

    if do_deploy:
        deploy_to_vercel()


if __name__ == "__main__":
    main()
