import requests

GOOGLE_API_KEY = "AIzaSyCIJfnUly0hq75Jtv_HsSr2g9V82ZKJ7bw"
SEARCH_ENGINE_ID = "7437a602cfa5e47de"


def search_google_pse(query: str):
    """
    Search products using Google Programmable Search Engine.
    Extracts structured product data from pagemap.
    """

    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": 10
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Log and handle API errors
    if "error" in data:
        error_msg = data["error"].get("message", "Unknown error")
        print(f"[Google PSE ERROR] {data['error'].get('code')}: {error_msg}")
        return [{"title": f"API Error: {error_msg}",
                 "link": "https://console.cloud.google.com/billing",
                 "image": None, "price": None, "rating": None,
                 "store": "Google API", "content": error_msg,
                 "source": "google_pse"}]

    results = []

    for item in data.get("items", []):

        pagemap = item.get("pagemap", {})

        # -------- Image --------
        image = None
        if "cse_image" in pagemap:
            image = pagemap["cse_image"][0].get("src")

        # -------- Price --------
        price = None
        offers = pagemap.get("offer", [])
        if offers:
            price_val = offers[0].get("price")
            currency = offers[0].get("pricecurrency", "")
            if price_val:
                price = f"{currency} {price_val}".strip()

        # -------- Rating --------
        rating_str = None
        ratings = pagemap.get("aggregaterating", [])
        if ratings:
            rating = ratings[0].get("ratingvalue")
            reviews = ratings[0].get("reviewcount")
            if rating:
                rating_str = f"{rating}/5"
                if reviews:
                    rating_str += f" ({reviews} reviews)"

        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "image": image,
            "price": price,
            "rating": rating_str,
            "store": item.get("displayLink"),
            "content": item.get("snippet"),
            "source": "google_pse",
        })

    return results