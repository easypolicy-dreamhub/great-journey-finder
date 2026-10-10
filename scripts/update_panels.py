import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

DATA_FILE = "data/panels.json"
TEMP_FILE = "data/panels_temp.json"


def update_panels():
  # 1. Load existing data as a safety backup fallback
  existing_data = {}
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    except:
      pass

  # Default structure for the 7 Great Journey categories
  providers_data = {
      "pharmacies": [],
      "clinics": [],
      "clinics_24hr": [],
      "vaccination": [],
      "hospitals": [],
      "hospitals_ae": [],
      "physio": [],
  }

  try:
    print("Checking Great Eastern locator page...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(
        "https://www.greateasternlife.com/my/en/customer-services/healthcare-services/healthcare-overview/locators-search-page.html",
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Scrape PDF links dynamically from the page
    for a in soup.find_all("a", href=True):
      href = a["href"]
      text = a.get_text().lower()

      # Match categories and store sample/download references
      if "pdf" in href.lower() or "pdf" in text:
        item = {
            "name": a.get_text().strip(),
            "state": "Malaysia",
            "address": "Official Great Eastern Panel PDF",
            "details": f"Download Link: {href if href.startswith('http') else 'https://www.greateasternlife.com' + href}",
        }

        if "pharmacy" in text:
          providers_data["pharmacies"].append(item)
        elif "24 hour" in text or "24-hour" in text:
          providers_data["clinics_24hr"].append(item)
        elif "vaccination" in text:
          providers_data["vaccination"].append(item)
        elif "physiotherapy" in text:
          providers_data["physio"].append(item)
        elif "hospital" in text and ("accident" in text or "emergency" in text):
          providers_data["hospitals_ae"].append(item)
        elif "hospital" in text:
          providers_data["hospitals"].append(item)
        elif "clinic" in text:
          providers_data["clinics"].append(item)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    final_output = {"last_updated": today_str, "providers": providers_data}

    os.makedirs("data", exist_ok=True)
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
      json.dump(final_output, f, ensure_ascii=False, indent=2)

    os.replace(TEMP_FILE, DATA_FILE)
    print("✅ Panel check and data sync completed successfully.")

  except Exception as e:
    print(f"❌ Error encountered: {e}")
    print("🛡️ Fail-safe activated: Preserving previous data.")
    if os.path.exists(TEMP_FILE):
      os.remove(TEMP_FILE)


if __name__ == "__main__":
  update_panels()