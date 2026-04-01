import re
import requests

# DataForSEO credentials — get from https://app.dataforseo.com/api-access
DATAFORSEO_LOGIN = "arjun.p@toobler.com"
DATAFORSEO_PASSWORD = "3e155272ccc0250e"


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

SKIP_URL_PATTERNS = [
    ".pdf", "/magazine", "/news", "/press", "/blog", "/about",
    "/contact", "/careers", "/history", "/heritage", "/media",
    "/sitemap", "/legal", "/privacy", "/terms", "/faq",
]

SKIP_TITLE_PATTERNS = [
    "[pdf]", "official website", "since 1", "homepage",
    "magazine", "press release", "news", "blog",
]


def _is_product_page(link: str, title: str) -> bool:
    """Filter out non-product pages."""
    link_lower = link.lower()
    title_lower = title.lower()

    for p in SKIP_URL_PATTERNS:
        if p in link_lower:
            return False
    for p in SKIP_TITLE_PATTERNS:
        if p in title_lower:
            return False

    # Skip root domain homepages
    path = link_lower.split("://")[-1].split("?")[0].rstrip("/")
    if len([s for s in path.split("/") if s]) <= 1:
        return False

    return True


def _match_store(link: str):
    for d in ALLOWED_DOMAINS:
        if d in link:
            key = d.replace(".com", "").replace(".net", "")
            return STORE_NAMES.get(key, key.capitalize())
    return None


def search_dataforseo(query: str):
    """
    Search products using DataForSEO Google Organic SERP API.
    Uses the Live/Advanced endpoint for synchronous results.
    Searches each allowed domain individually with site: operator.
    """
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    auth = (DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)

    per_domain_results = {}

    # Search each domain individually
    for domain in ALLOWED_DOMAINS:
        payload = [{
            "keyword": f"{query} site:{domain}",
            "location_name": "United States",
            "language_name": "English",
            "device": "desktop",
            "depth": 5,
        }]

        try:
            resp = requests.post(url, json=payload, auth=auth, timeout=15)
            data = resp.json()

            # Handle API errors
            if data.get("status_code") != 20000:
                error_msg = data.get("status_message", "Unknown error")
                print(f"[DataForSEO ERROR] {error_msg}")
                continue

            tasks = data.get("tasks", [])
            if not tasks:
                continue

            task = tasks[0]
            if task.get("status_code") != 20000:
                continue

            result_data = task.get("result", [])
            if not result_data:
                continue

            items = result_data[0].get("items", [])
            organic_items = [
                item for item in items
                if item.get("type") == "organic"
            ]

            if organic_items:
                per_domain_results[domain] = organic_items

        except Exception as e:
            print(f"[DataForSEO] Error searching {domain}: {e}")
            continue

    # Round-robin across domains
    results = []
    seen_links = set()

    for round_idx in range(3):
        for domain, items in per_domain_results.items():
            if len(results) >= 10:
                break
            if round_idx >= len(items):
                continue

            item = items[round_idx]
            link = item.get("url", "")
            title = item.get("title", "")

            if not link or link in seen_links:
                continue
            if not _is_product_page(link, title):
                continue

            store = _match_store(link)
            if not store:
                continue

            seen_links.add(link)

            # Price from description/snippet
            description = item.get("description", "")
            price_matches = PRICE_PATTERN.findall(description + " " + title)
            price = f"${price_matches[0]}" if price_matches else None

            # Rating from DataForSEO rating field
            rating_info = item.get("rating")
            rating_str = None
            if rating_info:
                rv = rating_info.get("rating_value")
                rc = rating_info.get("votes_count") or rating_info.get("rating_count")
                if rv:
                    rating_str = f"{rv}/5"
                    if rc:
                        rating_str += f" ({rc} reviews)"

            # Image — DataForSEO includes images in some results
            image = None
            images_list = item.get("images", [])
            if images_list and isinstance(images_list, list):
                image = images_list[0].get("url") if isinstance(images_list[0], dict) else images_list[0]

            # Fallback image from pre_snippet or breadcrumb
            if not image:
                pre_snippet = item.get("pre_snippet")
                if pre_snippet and isinstance(pre_snippet, str) and pre_snippet.startswith("http"):
                    image = pre_snippet

            results.append({
                "title": title,
                "link": link,
                "image": image,
                "price": price,
                "rating": rating_str,
                "store": store,
                "content": description[:200] + "..." if len(description) > 200 else description,
                "source": "dataforseo",
            })

    return results
