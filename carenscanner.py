import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import requests

# Instellingen
CARENPAGE_URL = "https://www.carenzorgt.nl/person/[ID hier]/dossier"
PROFILE_DIR = ".caren_profile"
ENTRIES_FILE = "entries.json"
SLEEP_INTERVAL = 600  # 10 minuten

# Twilio-config
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_FROM = ""
TWILIO_RECIPIENTS = ["+316........", "+316........", "+316........"]

# Helper
def save_entries(entries):
    with open(ENTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

def load_previous_entries():
    if not os.path.exists(ENTRIES_FILE):
        return []
    with open(ENTRIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def slimme_samenvatting(body, max_tekens=120):
    zinnen = body.split(". ")
    samenvatting = ". ".join(zinnen[:2]).strip()
    return samenvatting[:max_tekens - 3] + "..." if len(samenvatting) > max_tekens else samenvatting

def send_sms_alert(timestamp, body):
    try:
        dt = datetime.fromisoformat(timestamp)
        datum_tijd = dt.strftime("%d-%m %H:%M")
    except:
        datum_tijd = timestamp[:16]

    samenvatting = slimme_samenvatting(body)
    bericht = f" {datum_tijd} – {samenvatting}"

    for nummer in TWILIO_RECIPIENTS:
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
            data={"To": nummer, "From": TWILIO_FROM, "Body": bericht},
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        )

        if response.status_code in [200, 201]:
            print(f"SMS verzonden naar {nummer} ({len(bericht)} tekens).", flush=True)
        else:
            print(f"Fout bij verzenden naar {nummer}: {response.text}", flush=True)

        time.sleep(10)  # 10 seconden pauze tussen SMS'en

def parse_entries(page):
    entry_elements = page.locator("li.mod-dossier-entry")
    count = entry_elements.count()
    print(f"Gevonden rapportage-elementen: {count}", flush=True)
    results = []
    for i in range(count):
        item = entry_elements.nth(i)
        timestamp = item.locator("time").get_attribute("value")
        text = item.locator("p.rich-text").inner_text()
        results.append({"timestamp": timestamp, "body": text.strip()})
    return results

def find_new_entries(old_entries, new_entries):
    if not old_entries:
        return new_entries
    last_known = max(e["timestamp"] for e in old_entries)
    return [e for e in new_entries if e["timestamp"] > last_known]

def interactive_login():
    with sync_playwright() as p:
        print("Eerste keer inloggen: browser opent nu.", flush=True)
        browser = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)
        page = browser.new_page()
        page.goto(CARENPAGE_URL)
        input("Log in en druk Enter zodra je de dossierinhoud ziet.")
        browser.close()
        print("Profiel opgeslagen in:", PROFILE_DIR, flush=True)

def scrape_with_saved_session():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(PROFILE_DIR, headless=True)
        page = browser.new_page()
        try:
            page.goto(CARENPAGE_URL, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeout:
            print("Timeout bij laden van dossier.", flush=True)
            browser.close()
            return []
        entries = parse_entries(page)
        browser.close()
        return entries

#l00p
def main():
    if not os.path.exists(PROFILE_DIR):
        interactive_login()

    print("Start monitoring. Elke 10 minuten checken op nieuwe rapportages.", flush=True)

    baseline = scrape_with_saved_session()
    if not baseline:
        print("Geen data bij eerste check. Lege lijst opgeslagen, monitoring start alsnog.", flush=True)
        save_entries([])
    else:
        save_entries(baseline)
        print("Eerste snapshot opgeslagen.", flush=True)

        # Direct eerste SMS bij opstart
        laatste = sorted(baseline, key=lambda e: e["timestamp"])[-1]
        print(f"Eerste SMS bij opstart:\n {laatste['timestamp']}\n {laatste['body']}", flush=True)
        send_sms_alert(laatste["timestamp"], laatste["body"])

    while True:
        try:
            print(f"\n Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
            new_entries = scrape_with_saved_session()

            if not new_entries:
                print("Geen data opgehaald. Mogelijk sessie verlopen.", flush=True)
            else:
                old_entries = load_previous_entries()
                updates = find_new_entries(old_entries, new_entries)

                if updates:
                    print(f"{len(updates)} nieuwe rapportage(s) gevonden:", flush=True)
                    for entry in updates:
                        print(f"\n{entry['timestamp']}\n📝 {entry['body']}\n", flush=True)
                        send_sms_alert(entry['timestamp'], entry['body'])

                    save_entries(new_entries)
                else:
                    print("Geen nieuwe rapportages.", flush=True)

        except Exception as e:
            print(f"Fout tijdens scraping: {e}", flush=True)

        print(f"Wacht {SLEEP_INTERVAL // 60} minuten...\n", flush=True)
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
