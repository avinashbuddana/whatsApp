# WingerX WhatsApp CRM — Shree Gajanand Jewellers

**Client:** [Shree Gajanand Jewellers, Ranchi](https://shreegajanandjewellers.com/)  
**Provider:** WingerX by Neurixa Solutions  
**Deployment:** isolated, brand-new Render web service with its own database and Redis  
**Repository:** https://github.com/avinashbuddana/whatsApp

This is a WingerX-branded distribution of [Whatomate](https://github.com/shridarpatil/whatomate). It builds from pinned upstream source commit `88b0e856e8d2e111833a76bdaf4c3e0351768211` (2026-11-16) and applies the white WingerX UI while retaining the upstream Go backend and Vue functionality. **This repository is not an official GitHub fork**; it contains source overlays and a reproducible source build.

## Features retained
- WhatsApp Cloud API connection, Embedded Signup, webhooks, inbox and messaging
- Contacts and organizations, roles, teams, campaign CSV import and template sending
- Chatbots, flows, automation and analytics
- Auth, database migrations, Redis and background workers

## Branding
- White-first WingerX dashboard, login and inbox
- WingerX blue / deep navy controls
- Client-specific welcome message and Shree Gajanand Jewellers organization seed
- Official WingerX logo should replace the temporary `wingerx-mark.svg` before public delivery
- Browser title and favicon changed; no customer-specific message/contact data baked into source

## Deploy
Use Render Blueprint with:
- repo: `https://github.com/avinashbuddana/whatsApp`
- branch: `main`
- Blueprint path: `render.yaml`
- free service + free Postgres + free Key Value in Singapore
- admin email: `admin@admin.com`, admin password: randomly generated and stored only in Render Environment settings

The system starts with a **fresh database**, no connected Meta account, and no imported contacts, campaigns, chats or templates. Client connects their own WhatsApp Business account after first login. **Do not copy encryption keys or Meta credentials from the old test system.**

### For WhatsApp setup
Use **Settings → Accounts → Connect with Facebook** with properly configured Meta Embedded Signup values, or set up Cloud API credentials through the supported manual account screen. Configure callback URL to `https://<new-service>.onrender.com/api/webhook` in the client Meta app, and subscribe to `messages`. Config values for Embedded Signup are `WHATOMATE_WHATSAPP__APP_ID`, `WHATOMATE_WHATSAPP__APP_SECRET`, and `WHATOMATE_WHATSAPP__CONFIG_ID`. Do not put secrets in Git. The end client may need Meta App permissions and an app able to onboard their number.

### Before real customer traffic
This free deployment is a test environment. Free Postgres expires; free Redis does not persist data; local uploads are ephemeral, and the web service may sleep. Use paid persistent Render Postgres and Redis, configure durable S3-compatible media storage and backups, add monitoring, check WhatsApp rates/consent, and test inbound webhook delivery. The original platform's phone calling / IVR may need additional TURN/UDP infrastructure and is not guaranteed by a simple Render web service.

### Licensing
The source build uses upstream [Whatomate](https://github.com/shridarpatil/whatomate), licensed **AGPL-3.0**. Modifying and serving it over a network may require providing the corresponding source code and preserving notices. WingerX rebranding must not remove legal notices or required attribution. Seek licensing review before proprietary commercial distribution.

## Code layout
- `Dockerfile` — builds upstream Go/Vue source at pinned commit with WingerX branding
- `apply_branding.py` — fail-fast frontend source patch
- `wingerx.css` and `client.css` — styling
- `wingerx-mark.svg` — temporary brand mark
- `config.toml` — secret-free runtime defaults
- `render-start.sh` — Render PostgreSQL/Redis adapter
- `render.yaml` — isolated deployment resources

The old `whatomate-test` instance is **not** changed or deleted by this new deployment. Deleting its service/database requires a separate confirmation in the Render dashboard.
