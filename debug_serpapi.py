import json
from serpapi_service import search_serpapi, SERPAPI_KEY, SERPAPI_URL
import requests

def test_raw_serpapi():
    query = "gold ring with diamond under 3000"
    from serpapi_service import ALLOWED_DOMAINS
    site_filter = " OR ".join(f"site:{d}" for d in ALLOWED_DOMAINS)
    full_query  = f"{query} ({site_filter})"
    
    resp = requests.get(SERPAPI_URL, params={
        "engine": "google",
        "q": full_query,
        "api_key": SERPAPI_KEY,
        "num": 10,
        "gl": "us",
        "hl": "en",
    })
    data = resp.json()
    organic = data.get("organic_results", [])
    
    # Save all results
    with open("serpapi_all_results.json", "w") as f:
        json.dump(organic, f, indent=2)
            
if __name__ == "__main__":
    test_raw_serpapi()
