# FLEXR — Projekt-Setup für Claude Code

> **Weiterarbeiten auf einem anderen Gerät:** Den aktuellen Produktionsstand,
> Tests, offene Punkte, Build-/Deploy-Befehle und die sichere Übergabe an Claude
> Code beschreibt [HANDOFF.md](HANDOFF.md).

Dieses Verzeichnis ist der Startpunkt, um aus dem Chat-Prototyp eine echte,
deploybare App unter flexr.social zu machen. Öffne diesen Ordner in Claude
Code und lass es von hier aus weiterbauen.

## Tech-Stack (Vorschlag)

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy — passt zu deiner
  bestehenden Infrastruktur (Debian/Ubuntu VPS, Python-venvs, pm2), die du
  schon für `morpho_monitor.py` & Co. nutzt.
- **Datenbank:** PostgreSQL (lokal via Docker zum Entwickeln, auf dem VPS
  entweder nativ installiert oder als Docker-Container).
- **Fotos:** Objekt-Storage (Cloudflare R2 oder S3-kompatibel) statt
  Base64-in-DB — deutlich günstiger und schneller als das Artifact-Storage
  aus dem Prototyp.
- **Zahlungen:** Stripe Checkout + Billing Portal (Trial-Periode nativ
  unterstützt, SEPA + Kreditkarte für AT-Nutzer).
- **Prozess-Management:** pm2 (dein gewohntes Setup) startet den
  Uvicorn-Prozess, alternativ ein systemd-Unit (liegt unter `deploy/`).
- **Frontend:** vorerst weiterhin eine einzelne HTML/JS-Datei (aus dem
  Prototyp abgeleitet), die gegen die REST-API unter `/api/...` spricht.
  Kein Framework nötig für den aktuellen Funktionsumfang.

## Ordnerstruktur

```
flexr/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI-Einstiegspunkt, Rate-Limiter-Setup
│   │   ├── config.py          # Settings aus .env
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # User, Photo, Swipe, Match, Block, Report
│   │   ├── schemas.py         # Pydantic-Schemas (Request/Response)
│   │   ├── security.py        # Passwort-Hash, JWT/Session-Helper
│   │   ├── storage.py         # Presigned-URL-Erzeugung (S3/R2)
│   │   ├── rate_limit.py      # slowapi-Limiter-Instanz
│   │   ├── stripe_client.py   # Stripe Checkout + Webhook-Handling
│   │   └── routers/
│   │       ├── auth.py        # Registrierung/Login
│   │       ├── profiles.py    # Profil anlegen/bearbeiten/lesen, Foto-Upload
│   │       ├── swipes.py      # Like/Pass + Match-Erkennung
│   │       ├── matches.py     # Match-Liste
│   │       ├── billing.py     # Trial-Status, Stripe-Checkout, Webhook
│   │       └── safety.py      # Report/Block
│   ├── alembic/                # DB-Migrationen (alembic upgrade head)
│   ├── tests/                  # pytest-Suite (Auth, Swipes, Safety, Fotos)
│   ├── requirements.txt
│   ├── requirements-dev.txt    # + pytest, httpx (nur für Tests)
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── index.html              # oeffentliche Landingpage (deutsch)
│   ├── en/index.html           # englische Fassung — ERZEUGT, siehe build-en.py
│   ├── build-en.py             # erzeugt en/index.html aus index.html + Woerterbuch
│   ├── lang-switch.js          # Wegfuehrung zwischen / und /en/
│   ├── app/index.html          # Web-App, fetch()-basiert gegen /api/...
│   ├── i18n.js                 # Zweisprachigkeit der App: Maschinerie + Erkennung
│   ├── i18n-landing.js         # Woerterbuch der Landingpage (Eingabe fuer build-en.py)
│   └── app/i18n-app.js         # Woerterbuch der Web-App (de/en)
├── deploy/
│   ├── flexr-api.service       # systemd-Unit (Alternative zu pm2)
│   ├── ecosystem.config.js     # pm2-Konfiguration
│   └── nginx-flexr.conf        # Reverse Proxy + SSL-Hinweis
└── README.md
```

## Lokal starten (zum Testen, bevor es auf den VPS geht)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt   # zieht auch requirements.txt (inkl. pytest, httpx)
cp .env.example .env          # Werte eintragen (DB-URL, Stripe-Keys, JWT-Secret, S3/R2)
alembic upgrade head          # Tabellen anlegen (ersetzt das frühere create_all())
uvicorn app.main:app --reload --port 8000
```

Postgres lokal per Docker, falls du keins installiert hast:

```bash
docker run --name flexr-db -e POSTGRES_PASSWORD=flexr -e POSTGRES_DB=flexr \
  -p 5432:5432 -d postgres:16
```

Tests laufen mit SQLite in-memory, brauchen also keine echte Datenbank:

```bash
python -m pytest
```

Frontend lokal separat ausliefern (z. B. auf Port 5173, ist in der CORS-Whitelist
in `main.py` bereits enthalten) und gegen das Backend auf Port 8000 testen:

```bash
cd frontend
python3 -m http.server 5173
```

Für neue DB-Änderungen an `models.py` eine neue Migration erzeugen:

```bash
alembic revision --autogenerate -m "kurze beschreibung"
alembic upgrade head
```

## Deploy auf deinen VPS (grobe Reihenfolge)

Dieses gesamte Projekt (der `flexr/`-Ordner, so wie er hier vorliegt) kommt
1:1 nach `/flexr` auf deinem VPS. Alle Pfade in `deploy/` sind bereits darauf
eingestellt.

```bash
# gesamten Ordnerinhalt nach /flexr auf den VPS bringen, z.B.:
scp -r flexr/* dein-user@dein-vps:/flexr/
# oder, falls du ein Git-Repo daraus machst:
git clone <dein-repo> /flexr

sudo chown -R $USER:$USER /flexr   # Besitzrechte, falls als root angelegt
```

1. `cd /flexr/backend && python3 -m venv venv && source venv/bin/activate`
   `&& pip install -r requirements.txt`
2. Postgres auf dem VPS einrichten (nativ oder Docker), `/flexr/backend/.env`
   aus `.env.example` mit Produktionswerten befüllen (inkl. echtem S3/R2-Bucket
   für Fotos), danach `alembic upgrade head` laufen lassen
3. Uvicorn über pm2 starten: `pm2 start /flexr/deploy/ecosystem.config.js`
   (Alternative: `deploy/flexr-api.service` mit systemd — vorher
   `sudo cp /flexr/deploy/flexr-api.service /etc/systemd/system/` und
   `sudo systemctl enable --now flexr-api`)
   Für Erinnerungen zum kostenlosen Probemonat zusätzlich
   `deploy/flexr-email-jobs.service` und `deploy/flexr-email-jobs.timer` nach
   `/etc/systemd/system/` kopieren und den Timer mit
   `sudo systemctl enable --now flexr-email-jobs.timer` aktivieren.
4. nginx als Reverse Proxy vor Uvicorn schalten:
   `sudo cp /flexr/deploy/nginx-flexr.conf /etc/nginx/sites-available/flexr.social`
   `&& sudo ln -s /etc/nginx/sites-available/flexr.social /etc/nginx/sites-enabled/`
   `&& sudo nginx -t && sudo systemctl reload nginx`,
   danach SSL via `certbot --nginx -d flexr.social -d www.flexr.social`
5. DNS bei deinem Domain-Registrar: A-Record von `flexr.social` auf die
   IP deines VPS zeigen lassen (bzw. AAAA für IPv6, falls vorhanden)
6. Stripe: Live-Keys eintragen, Webhook-Endpoint `https://flexr.social/api/billing/webhook`
   im Stripe-Dashboard hinterlegen. **Seit 07.09.2026 ist die Abogebühr
   ausgesetzt** (`BILLING_ENABLED=false`, Standard): FLEXR ist für alle
   kostenlos, der Checkout lehnt mit 409 ab, die Bezahlwand greift nicht und
   die Probemonat-Erinnerungen aus Punkt 3 entfallen. Der komplette
   Stripe-Pfad bleibt im Code — `BILLING_ENABLED=true` schaltet ihn wieder
   scharf (siehe `backend/app/config.py`).
7. Vor dem Live-Schalten: Impressum, Datenschutzerklärung, AGB und
   Altersverifikation ergänzen (in AT/EU bei einer Dating-Plattform mit
   Nutzerfotos Pflicht, kein optionales Nice-to-have). Melde-/Blockfunktion
   ist bereits vorhanden (`POST /api/reports`, `POST /api/blocks`).

## Offene Punkte (bewusst nicht in diesem Scaffold gelöst)

- E-Mail-Versand für Magic-Link-Login (z. B. über Postmark/SES) — aktuell
  passwortbasierte Anmeldung, kein Magic-Link-Mechanismus vorhanden
- Echtzeit-Chat zwischen Matches (aktuell nicht vorgesehen, v2)
- Account-Löschung durch den Nutzer selbst (kein DELETE-Endpoint; aktuell
  nur "Ausloggen" im Frontend)
- Echter S3/R2-Bucket samt Zugangsdaten für den Foto-Upload (Presigned-URL-Flow
  ist implementiert und getestet, braucht aber einen echten Bucket, siehe
  `S3_*`-Variablen in `.env.example`)
- Legal: Impressum, Datenschutzerklärung, AGB, Altersverifikation — vor dem
  Live-Schalten in AT/EU für eine Dating-Plattform mit Nutzerfotos Pflicht,
  hier bewusst nicht vorformuliert (echte Firmendaten nötig)
