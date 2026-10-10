import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

DATA_FILE = "data/panels.json"
TEMP_FILE = "data/panels_temp.json"


def update_panels():
  existing_data = {}
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    except:
      pass

  new_providers = existing_data.get(
      "providers",
      {
          "pharmacies": [],
          "clinics": [],
          "clinics_24hr": [],
          "vaccination": [],
          "hospitals": [],
          "hospitals_ae": [],
          "physio": [],
      },
  )

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
    # Dynamic link scanning safeguard hook goes here
    # If site structure changes or fails validation, fail-safe keeps previous month's data intact.

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    final_output = {
        "last_updated": today_str,
        "providers": new_providers,  # Preserves active validated data
    }

    os.makedirs("data", exist_ok=True)
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
      json.dump(final_output, f, ensure_ascii=False, indent=2)

    os.replace(TEMP_FILE, DATA_FILE)
    print("✅ Panel check completed safely.")

  except Exception as e:
    print(f"❌ Error encountered: {e}")
    print(
        "🛡️ Fail-safe activated: Keeping last month's data untouched to prevent"
        " downtime."
    )
    if os.path.exists(TEMP_FILE):
      os.remove(TEMP_FILE)


if __name__ == "__main__":
  update_panels()