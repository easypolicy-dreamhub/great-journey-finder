# The Great Journey Finder

A phone-friendly finder for Great Eastern's **The Great Journey** panel: hospitals (with A&E outpatient flag),
clinics (with 24-hour flag), pharmacies, physiotherapy centres and the 2026 vaccination programme clinics.

## What's inside
- `index.html` - the whole app
- `data/` - `hospitals.json`, `clinics.json`, `pharmacies.json`, `physio.json`, `vaccination.json`, `meta.json` (rebuilt automatically)
- `scripts/update_data.py` - finds the current PDF links on Great Eastern's locator page, downloads them and rebuilds `data/`
- `.github/workflows/update-monthly.yml` - runs the script on the 1st and 16th of every month (and on demand: Actions tab > Run workflow)

## How the automatic update behaves
- The three core lists (hospital, clinic, pharmacy, physio) must be found, or the run stops and nothing is changed.
- A&E, 24-hour and vaccination lists are optional: if Great Eastern removes one, last month's data is kept.
- If a PDF changes format and far fewer records are read than before, the run refuses to overwrite the data.
- A failed run never breaks the site; it simply keeps showing the previous data. GitHub emails you when a run fails.
- The list of 12 A&E covered diagnoses is a picture inside Great Eastern's PDF, so it is kept in the script (`DEFAULT_AE_DIAGNOSES`).
- Distances are approximate: each address is placed at its town centre, not at the building.
