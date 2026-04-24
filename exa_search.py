import re
import requests

EXA_API_KEY = "ec7e77cc-7d2e-4122-bd79-2b0f351c1699"


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

# Extended price patterns to catch more formats
PRICE_PATTERN = re.compile(
    r"(?:"
    r"USD\s*[\d,]+(?:\.\d{1,2})?|"          # USD 1,234.00
    r"US\$\s*[\d,]+(?:\.\d{1,2})?|"         # US$ 1,234
    r"\$\s*[\d,]+(?:\.\d{1,2})?|"           # $1,234.00
    r"€\s*[\d,]+(?:\.\d{1,2})?|"            # €1,234
    r"£\s*[\d,]+(?:\.\d{1,2})?|"            # £1,234
    r"Price[:\s]+[\$€£]?\s*[\d,]+(?:\.\d{1,2})?|"  # Price: $1,234
    r"[\d,]+(?:\.\d{1,2})?\s*USD"           # 1,234.00 USD
    r")",
    re.IGNORECASE
)


def _match_store(link: str):
    for d in ALLOWED_DOMAINS:
        if d in link:
            key = d.replace(".com", "").replace(".net", "")
            return STORE_NAMES.get(key, key.capitalize())
    return None


def _extract_price(text: str):
    """Extract and clean price from text."""
    if not text:
        return None
    matches = PRICE_PATTERN.findall(text)
    for match in matches:
        # Clean up the match
        digits = re.sub(r"[^\d,.]", "", match)
        if digits and len(digits) >= 3:  # avoid single digit false positives
            return f"${digits}"
    return None


def search_exa(query: str):
    url = "https://api.exa.ai/search"

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "numResults": 10,
        "includeDomains": ALLOWED_DOMAINS,
        "type": "neural",
        "livecrawl": "always",              # ← MUST be top-level, NOT inside contents
        "contents": {
            "text": {
                "maxCharacters": 2000
            },
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Exa API error: {e}")
        return []

    results = []

    for item in data.get("results", []):
        link = item.get("url", "")
        store = _match_store(link)
        if not store:
            continue

        snippet = item.get("text", "")
        title = item.get("title", "")

        # Try price from full crawled text first, then title
        price = _extract_price(snippet) or _extract_price(title)

        results.append({
            "title": title,
            "link": link,
            "image": item.get("image"),
            "price": price,
            "rating": None,
            "store": store,
            "content": snippet[:300] if snippet else "",
            "source": "exa",
        })

    return results