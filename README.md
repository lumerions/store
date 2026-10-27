<h1 align="center">Store System</h1>

<p align="center">
  A FastAPI-powered storefront for selling physical items, with crypto checkout, email verification, and an admin panel.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/crypto-NOWPayments-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white" alt="NOWPayments">
  <img src="https://img.shields.io/badge/deployed%20on-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Jinja2-B41717?logo=jinja&logoColor=white" alt="Jinja2">
  <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white" alt="Pydantic">
  <img src="https://img.shields.io/badge/Resend-000000?logo=resend&logoColor=white" alt="Resend">
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#project-structure">Structure</a>
</p>

> [!WARNING]
> Crypto is the only supported payment method, and invoice creation is currently broken. You will need to fix it yourself.

---

## Features

- **Storefront**: product catalog and product pages for real-world items (e.g. shirts), with on-sale/off-sale toggling
- **User authentication**: signup/login with bcrypt-hashed passwords and cookie-based sessions
- **Email verification and one-time login codes**: sent through Resend, valid for 15 minutes
- **Crypto checkout**: NOWPayments invoices and an HMAC-verified IPN webhook that records completed orders
- **Order history**: customers can view purchases and delivery status, and opt in or out of order emails
- **Admin panel**: add and edit items, lock or unlock accounts, and view and deliver pending orders
- **Caching**: store data and per-session data cached in Upstash Redis
- **Rate limiting**: per-IP limits with SlowAPI
- **Auto docs**: Swagger UI at `/docs`

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic |
| Templates | Jinja2 + static JS in `javascript/` and CSS in `css/` |
| Database | PostgreSQL (`psycopg`): accounts, store items, orders, purchases |
| Cache and sessions | Upstash Redis |
| Payments | NOWPayments (crypto invoices + IPN webhook) |
| Email | Resend |
| Hosting | Vercel |

## Installation

```bash
git clone https://github.com/lumerions/store.git
cd store
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the dev server:

```bash
uvicorn main:app --reload
```

Then open <http://localhost:8000>.

## Configuration

Settings are loaded through `lib/config.py`. Set these environment variables before starting the app (verify the exact names there):

| Variable | Description |
|---|---|
| `STORE_NAME` | Display name used in titles and emails |
| `ADMIN_USERNAME` | Username granted access to `/admin` |
| `POSTGRES_DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Upstash Redis REST URL |
| `REDIS_TOKEN` | Upstash Redis REST token |
| `RESEND_API_KEY` | Resend API key for verification and OTP emails |
| `NOWPAYMENTS_API_SECRET` | NOWPayments API key, used to create invoices |
| `NOWPAYMENTS_IPN_SECRET` | NOWPayments IPN secret, used to verify webhook signatures |

You'll also need to:

- Set the `ipn_callback_url` in `main.py` to your own deployed `/api/cryptobuy` endpoint
- Replace the sender addresses in `sendEmail(...)` with a domain verified in Resend
- Set the supported coins list in your config

## Project Structure

```
store/
├── main.py            # FastAPI app and all routes
├── lib/               # config, Postgres/Redis clients, schemas, helpers
├── templates/         # Jinja2 HTML pages (index, product, purchases, settings, admin...)
├── javascript/        # client-side scripts
├── css/               # stylesheets
├── public/            # static assets
├── requirements.txt
└── .gitignore
```
