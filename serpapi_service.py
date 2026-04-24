import re
import requests
from urllib.parse import urlparse

SERPAPI_KEY = "76bc9a3202a67b46af213db661e86ccb465d4f6ed822bcc69b94d69c0f74f894"

SERPAPI_URL = "https://serpapi.com/search"

# -------------------------------------------------
# Allowed domains
# -------------------------------------------------
ALLOWED_DOMAINS = [
    "cartier.com", "vancleefarpels.com", "boucheron.com", "chaumet.com", "mellerio.fr",
    "mauboussin.com", "fred.com", "repossi.com", "bulgari.com", "buccellati.com",
    "pomellato.com", "graff.com", "boodles.com", "garrard.com", "asprey.com",
    "debeers.com", "chopard.com", "piaget.com", "harrywinston.com", "tiffany.com",
    "davidyurman.com", "mikimoto.com", "patek.com", "rolex.com", "audemarspiguet.com",
    "vacheron-constantin.com", "messika.com", "dior.com", "chanel.com", "gucci.com",
    "us.louisvuitton.com", "hermes.com", "lorraineschwartzjewels.com", "hemmerle.com",
    "wallacechan.com", "qeelin.com", "fernandojorge.co.uk", "jessicamccormack.com",
    "marcobicego.com", "pasqualebruni.com", "robertocoin.com", "vhernier.com",
    "georgjensen.com", "olelynggaard.com", "sophiebillebrahe.com", "niwaka.com",
    "tasaki.co.jp", "hstern.com", "ippolita.com", "lagos.com", "johnhardy.com",
    "tacori.com", "verragio.com", "simong.com", "gabrielny.com", "neillanejewelry.com",
    "brilliantearth.com", "bluenile.com", "jamesallen.com", "whiteflash.com",
    "cleanorigin.com", "vrai.com", "mejuri.com", "catbirdnyc.com", "gorjana.com",
    "monicavinader.com", "kendrascott.com", "zoechicco.com", "anitako.com",
    "foundrae.com", "alisonlou.com", "lizziemandler.com", "marlaaaron.com",
    "loganhollowell.com", "marlolaz.com", "spinellikilcollin.com", "charlottechesnais.fr",
    "persee-paris.com", "wwake.com", "nadineghosn.com", "anakhouri.com", "jadetrau.com",
    "jemmawynne.com", "omegawatches.com", "jaeger-lecoultre.com", "breguet.com",
    "richardmille.com", "hublot.com", "fredleighton.com", "siegelson.com",
    "doyledoyle.com", "ireneneuwithjewelry.com", "prounisjewelry.com", "tanishq.co.in",
    "malabargoldanddiamonds.com", "amrapalijewels.com", "damasjewellery.com",
    "mouawad.com", "forevermark.com", "levian.com", "kwiat.com", "kay.com",
    "zales.com", "alexandani.com", "baublebar.com"
]


# -------------------------------------------------
# Domain filter
# -------------------------------------------------
def _is_allowed(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.replace("www.", "")
        return any(netloc == d or netloc.endswith("." + d) for d in ALLOWED_DOMAINS)
    except:
        return False


# -------------------------------------------------
# Extract OG Image from product page
# -------------------------------------------------
def _extract_og_image(html: str) -> str | None:

    # 1. OG meta tags
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+itemprop=["\']image["\'][^>]+content=["\']([^"\']+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)

    # 2. JSON-LD (MOST IMPORTANT)
    json_match = re.search(
        r'"image"\s*:\s*\[\s*"([^"]+)"',
        html
    )
    if json_match:
        return json_match.group(1)

    json_match = re.search(
        r'"image"\s*:\s*"([^"]+)"',
        html
    )
    if json_match:
        return json_match.group(1)

    # 3. Next.js __NEXT_DATA__ fallback
    next_match = re.search(
        r'"src"\s*:\s*"([^"]+\.(jpg|jpeg|png|webp))"',
        html,
        re.IGNORECASE
    )
    if next_match:
        return next_match.group(1)

    return None


# -------------------------------------------------
# Extract price from page (optional)
# -------------------------------------------------
PRICE_PATTERN = re.compile(
    r"(?:USD\s*|US\$\s*|\$\s*|€\s*|£\s*)([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE
)


def _extract_price(html: str):
    match = PRICE_PATTERN.search(html)
    if match:
        return match.group(0)
    return None


# -------------------------------------------------
# SERPAPI ORGANIC SEARCH
# -------------------------------------------------
def search_serpapi(query: str) -> list[dict]:

    site_filter = " OR ".join(f"site:{d}" for d in ALLOWED_DOMAINS)
    full_query = f"{query} ({site_filter})"

    try:
        resp = requests.get(
            SERPAPI_URL,
            params={
                "engine": "google",
                "q": full_query,
                "api_key": SERPAPI_KEY,
                "num": 15,
                "gl": "us",
                "hl": "en"
            },
            timeout=20
        )

        resp.raise_for_status()
        data = resp.json()

    except Exception as e:
        print("Search failed:", e)
        return []

    results = []

    for item in data.get("organic_results", []):

        link = item.get("link")

        if not link or not _is_allowed(link):
            continue

        try:
            headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive"
}


            page = requests.get(link, headers=headers, timeout=15)

            if page.status_code != 200:
                continue

            html = page.text

            image = _extract_og_image(html)
            price = _extract_price(html)

            results.append({
                "title": item.get("title"),
                "link": link,
                "image": image,
                "price": price,
                "store": urlparse(link).netloc.replace("www.", "")
            })

        except Exception:
            continue

        if len(results) >= 10:
            break

    return results


# -------------------------------------------------
# TEST
# -------------------------------------------------
if __name__ == "__main__":

    query = "diamond engagement ring"

    print(f"\nSearching for: {query}")
    print("-" * 50)

    items = search_serpapi(query)

    if not items:
        print("No results found.")
    else:
        for i, item in enumerate(items, 1):
            print(f"\n[{i}] {item['title']}")
            print(f"Store : {item['store']}")
            print(f"Price : {item['price'] or 'N/A'}")
            print(f"Image : {item['image'] or 'No image'}")
            print(f"Link  : {item['link']}")