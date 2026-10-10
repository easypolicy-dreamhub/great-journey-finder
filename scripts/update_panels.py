import datetime
import json
import os

DATA_FILE = "data/panels.json"
TEMP_FILE = "data/panels_temp.json"


def update_panels():
  # Direct links to Great Eastern's 7 Great Journey PDFs
  providers_data = {
      "pharmacies": [{
          "name": "The Great Journey Pharmacy List",
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-pharmacy-list.pdf"
          ),
      }],
      "clinics": [{
          "name": "The Great Journey Clinic List",
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-clinic-list.pdf"
          ),
      }],
      "clinics_24hr": [{
          "name": "The Great Journey Clinic List (24 Hours)",
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-clinic-list-24-hours.pdf"
          ),
      }],
      "vaccination": [{
          "name": (
              "The Great Journey Clinic (for Vaccination Health Programme 2026)"
              " List"
          ),
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-clinic-vaccination-programme-list.pdf"
          ),
      }],
      "hospitals": [{
          "name": "The Great Journey Hospital List",
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-hospital-list.pdf"
          ),
      }],
      "hospitals_ae": [{
          "name": (
              "The Great Journey Hospital (for Accident and Emergency"
              " Outpatient Treatment) List"
          ),
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-hospital-ae-list.pdf"
          ),
      }],
      "physio": [{
          "name": "The Great Journey Physiotherapy Centre List",
          "state": "Malaysia (All States)",
          "address": "Official PDF Directory",
          "details": (
              "https://www.greateasternlife.com/content/dam/greateasternlife/malaysia/english/customer-services/healthcare-services/healthcare-overview/pdf/the-great-journey-physiotherapy-centre-list.pdf"
          ),
      }],
  }

  today_str = datetime.date.today().strftime("%Y-%m-%d")
  final_output = {"last_updated": today_str, "providers": providers_data}

  os.makedirs("data", exist_ok=True)
  with open(TEMP_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

  os.replace(TEMP_FILE, DATA_FILE)
  print("✅ Data updated successfully.")


if __name__ == "__main__":
  update_panels()
