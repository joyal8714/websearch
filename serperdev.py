import re
import requests

SERPER_API_KEY = "6c0f56c004ab7d8fc125d103b9123704a02ef2f8"

ALLOWED_DOMAINS = [
    "anakhouri.com",
    "jadetrau.com",
    "jemmawynne.com",
    "omegawatches.com",
    "jaeger-lecoultre.com",
    "breguet.com",
    "richardmille.com",
    "hublot.com",
    "fredleighton.com",
    "siegelson.com",
    "doyledoyle.com",
]

STORE_NAMES = {
    "anakhouri": "Ana Khouri",
    "jadetrau": "Jade Trau",
    "jemmawynne": "Jemma Wynne",
    "omegawatches": "Omega Watches",
    "jaeger-lecoultre": "Jaeger-LeCoultre",
    "breguet": "Breguet",
    "richardmille": "Richard Mille",
    "hublot": "Hublot",
    "fredleighton": "Fred Leighton",
    "siegelson": "Siegelson",
    "doyledoyle": "Doyle & Doyle",
}

PRICE_PATTERN = re.compile(
    r"(?:USD\s*|US\$\s*|\$\s*|€\s*|£\s*)([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE
)

# URL patterns that are NOT product pages — skip these
SKIP_URL_PATTERNS = [
    ".pdf", "/magazine", "/news", "/press", "/blog", "/about",
    "/contact", "/careers", "/history", "/heritage", "/media",
    "/sitemap", "/legal", "/privacy", "/terms", "/faq",
    "/homepage", "/home", "/?", "/#",
]

# Titles that indicate non-product pages
SKIP_TITLE_PATTERNS = [
    "[pdf]", "official website", "since 1", "homepage",
    "magazine", "press release", "news", "blog",
    "about us", "contact", "careers",
]


def _is_product_page(link: str, title: str) -> bool:
    """Filter out PDFs, homepages, blog posts, and other non-product pages."""
    link_lower = link.lower()
    title_lower = title.lower()

    for pattern in SKIP_URL_PATTERNS:
        if pattern in link_lower:
            return False

    for pattern in SKIP_TITLE_PATTERNS:
        if pattern in title_lower:
            return False

    # Skip root domain homepages (e.g. https://www.hublot.com or https://www.hublot.com/)
    path = link_lower.split("://")[-1]          # strip scheme
    path = path.split("?")[0].rstrip("/")       # strip query + trailing slash
    segments = [s for s in path.split("/") if s]
    # If only 1 segment (the domain itself) or 2 segments (domain + one top-level page), skip
    domain_only = len(segments) <= 1
    if domain_only:
        return False

    return True


def _match_store(link: str):
    for d in ALLOWED_DOMAINS:
        if d in link:
            key = d.replace(".com", "").replace(".net", "")
            return STORE_NAMES.get(key, key.capitalize())
    return None


def _fetch_images_per_domain(query: str, domain: str, headers: dict, num: int = 5) -> list:
    """Fetch images restricted to a specific domain for better image-to-result matching."""
    try:
        resp = requests.post("https://google.serper.dev/images", headers=headers, json={
            "q": f"{query} site:{domain}",
            "gl": "us",
            "hl": "en",
            "num": num,
        })
        return [
            img.get("imageUrl") or img.get("thumbnailUrl")
            for img in resp.json().get("images", [])
            if (img.get("imageUrl") or img.get("thumbnailUrl"))
            and not (img.get("imageUrl") or img.get("thumbnailUrl", "")).endswith(".svg")
        ]
    except Exception:
        return []


def search_serper(query: str):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    per_domain_results = {}   # domain -> list of clean organic items
    per_domain_images = {}    # domain -> list of image URLs

    for domain in ALLOWED_DOMAINS:
        # ── Organic search for this domain ──
        site_query = f"{query} site:{domain}"
        try:
            resp = requests.post("https://google.serper.dev/search", headers=headers, json={
                "q": site_query,
                "gl": "us",
                "hl": "en",
                "num": 5,   # fetch 5, we'll filter down to real product pages
            })
            organic_raw = resp.json().get("organic", [])
        except Exception:
            organic_raw = []

        # Filter to actual product pages only
        clean = []
        for item in organic_raw:
            link = item.get("link", "")
            title = item.get("title", "")
            if _is_product_page(link, title):
                clean.append(item)

        if clean:
            per_domain_results[domain] = clean

        # ── Images for this domain ──
        per_domain_images[domain] = _fetch_images_per_domain(query, domain, headers, num=3)

    # ── Build final results: round-robin across domains ──
    results = []
    seen_links = set()
    max_rounds = 3

    for round_idx in range(max_rounds):
        for domain, items in per_domain_results.items():
            if len(results) >= 10:
                break
            if round_idx >= len(items):
                continue

            item = items[round_idx]
            link = item.get("link", "")
            if not link or link in seen_links:
                continue

            store = _match_store(link)
            if not store:
                continue

            seen_links.add(link)

            snippet = item.get("snippet", "")
            title = item.get("title", "")

            # Price from snippet or title
            price_matches = PRICE_PATTERN.findall(snippet + " " + title)
            price = f"${price_matches[0]}" if price_matches else None

            # Image: use domain-specific pool for correct match
            domain_images = per_domain_images.get(domain, [])
            image = domain_images.pop(0) if domain_images else None

            results.append({
                "title": title,
                "link": link,
                "image": image,
                "price": price,
                "rating": None,
                "store": store,
                "content": snippet,
                "source": "serper",
            })

    return results