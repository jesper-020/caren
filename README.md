# CarenZorgt Dossier Scanner

Python-script dat elke 10 minuten controleert op nieuwe rapportages in een CarenZorgt-dossier. Bij nieuwe entries wordt automatisch een SMS verstuurd via Twilio (of gebruik een andere sms-gateway api).

## Functionaliteit

- Laadt de dossierpagina van CarenZorgt (met opgeslagen sessie)
- Parsed alle rapportages
- Vergelijkt met eerdere entries
- Stuurt SMS bij nieuwe rapportage(s)

## Installatie
pip install playwright
playwright install

## Setup

1. Vul de `CARENPAGE_URL` in met het juiste persoons-ID, bijv:
   ```python
   CARENPAGE_URL = "https://www.carenzorgt.nl/person/1234567/dossier"
   
2. Vul de Twilio-gegevens in:
   ```python
   TWILIO_ACCOUNT_SID = "..."
   TWILIO_AUTH_TOKEN = "..."
   TWILIO_FROM = "+1..."
   TWILIO_RECIPIENTS = ["+316..."]
   
3. Run 
python carenzorgt_monitor.py

## Eerste run

Start het script gewoon via python carenzorgt_monitor.py.
Er opent een browservenster (niet headless).

Log in op CarenZorgt:
Typ je e-mailadres en wachtwoord

Zet een vinkje bij "Blijf ingelogd"
Klik op "Inloggen"
Wacht tot je op de dossierpagina bent en de rapportages zichtbaar zijn.
Ga dan terug naar de terminal en druk op Enter.
Dat is alles. Het script slaat de sessie lokaal op in .caren_profile/, zodat je de volgende keren automatisch ingelogd bent. Je hoeft daarna dus niks meer handmatig te doen zolang die sessie geldig blijft.
