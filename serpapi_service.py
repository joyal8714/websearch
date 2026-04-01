import re
import requests

SERPAPI_KEY = "ea692e4bf3ddc450de2032ddc0abe96eeccd2e88d6325dfdea5c4fa3c5bc70e6"

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


def _match_store(link: str):
    """Get store display name from link URL."""
    for d in ALLOWED_DOMAINS:
        if d in link:
            key = d.replace(".com", "").replace(".net", "")
            return STORE_NAMES.get(key, key.capitalize())
    return None


def _fetch_images(query: str, site_filter: str) -> list[str]:
    """Fetch product images from Google Images with site restriction."""
    try:
        resp = requests.get("https://serpapi.com/search", params={
            "engine": "google_images",
            "q": f"{query} {site_filter}",
            "api_key": SERPAPI_KEY,
            "num": 20,
            "gl": "us",
            "hl": "en",
        })
        data = resp.json()
        return [
            img.get("thumbnail") or img.get("original")
            for img in data.get("images_results", [])
            if img.get("thumbnail") or img.get("original")
        ]
    except Exception:
        return []


def search_serpapi(query: str):
    """
    Use Google organic engine with site: operator restricted to
    allowed luxury domains. Searches each domain individually so
    all stores get represented.
    """
    url = "https://serpapi.com/search"

    results = []
    per_domain_results = {}

    # Search each domain individually (top 3 per domain)
    for domain in ALLOWED_DOMAINS:
        try:
            resp = requests.get(url, params={
                "engine": "google",
                "q": f"{query} site:{domain}",
                "api_key": SERPAPI_KEY,
                "num": 3,
                "gl": "us",
                "hl": "en",
            })
            organic = resp.json().get("organic_results", [])
            if organic:
                per_domain_results[domain] = organic
        except Exception:
            continue

    # Round-robin: 1 result per domain per round, up to 10 total
    seen_links = set()
    for round_idx in range(3):
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

            # Price from rich_snippet or snippet text
            rich = item.get("rich_snippet", {})
            det = rich.get("bottom", {}).get("detected_extensions", {})
            price = det.get("price")
            if price and not str(price).startswith("$"):
                price = f"${price}"

            if not price:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                matches = PRICE_PATTERN.findall(snippet + " " + title)
                if matches:
                    price = f"${matches[0]}"

            # Rating from rich_snippet
            rating = det.get("rating")
            reviews = det.get("reviews")
            rating_str = None
            if rating:
                rating_str = f"{rating}/5"
                if reviews:
                    rating_str += f" ({reviews} reviews)"

            results.append({
                "title": item.get("title"),
                "link": link,
                "image": None,  # filled below
                "price": price,
                "rating": rating_str,
                "store": store,
                "content": item.get("snippet"),
                "source": "serpapi",
            })

    # Fetch images in one batch
    if results:
        site_filter = " OR ".join(f"site:{d}" for d in ALLOWED_DOMAINS)
        images = _fetch_images(query, site_filter)

        for result in results:
            # Try domain-matched image first
            domain_key = None
            for d in ALLOWED_DOMAINS:
                if d in result["link"]:
                    domain_key = d
                    break

            matched_image = None
            if domain_key:
                for img_url in images:
                    if domain_key in (img_url or ""):
                        matched_image = img_url
                        images.remove(img_url)
                        break

            if not matched_image and images:
                matched_image = images.pop(0)

            result["image"] = matched_image

    return results