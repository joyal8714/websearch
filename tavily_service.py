import re
import requests

TAVILY_API_KEY = "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"


ALLOWED_DOMAINS = [
    "anakhouri.com", "jadetrau.com", "jemmawynne.com",
    "omegawatches.com", "jaeger-lecoultre.com", "breguet.com",
    "richardmille.com", "hublot.com", "fredleighton.com",
    "siegelson.com", "doyledoyle.com",
]

# Broadened Regex: Now catches $, €, £, Rs, and ₹
PRICE_PATTERN = re.compile(
    r"(?:Rs\.?|₹|\$|€|£)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE
)

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

def search_tavily(query: str):
    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_images": True,
        "include_domains": ALLOWED_DOMAINS,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Check for API errors
        data = response.json()
    except Exception as e:
        print(f"API Request Failed: {e}")
        return []

    # Tavily returns a flat list of images.
    top_images = data.get("images", [])
    results = []

    for idx, r in enumerate(data.get("results", [])):
        url_str = r.get("url", "")
        content = r.get("content", "")

        # Store name with proper display names
        try:
            domain = url_str.split("/")[2] if "/" in url_str else "unknown"
            key = domain.replace("www.", "").split(".")[0]
            store = STORE_NAMES.get(key, key.capitalize())
        except (IndexError, AttributeError):
            store = "unknown"

        # Image Fallback: Safely try to assign an image from the flat list
        image = None
        if idx < len(top_images):
            image = top_images[idx]

        # Extract Price using the broadened regex
        price = None
        if content:
            # Find price WITH the currency symbol
            price_with_symbol = re.search(
                r"((?:Rs\.?|₹|\$|€|£)\s*[\d,]+(?:\.\d{1,2})?)", content, re.IGNORECASE
            )
            if price_with_symbol:
                price = price_with_symbol.group(1).strip()

        results.append({
            "title": r.get("title", "Unknown"),
            "link": url_str,
            "image": image,
            "price": price,
            "content": content[:200] + "..." if content else "",
            "store": store,
            "source": "tavily",
        })

    return results

# Test the function
# print(search_tavily("Omega Speedmaster watch price"))