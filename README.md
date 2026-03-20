# Neon Roo Computers & Upgrades

A production-ready Flask starter for a computer repair, PC upgrade, custom build, and tech support business.

## What changed in this build

- Brighter, more customer-facing landing page
- Improved navbar with your Neon Roo logo
- Cleaner footer and stronger calls to action
- Better accessibility and focus states
- Environment-based production config
- Gunicorn entrypoint and config
- Dockerfile and Procfile
- Reverse-proxy-safe Flask setup with `ProxyFix`
- Custom 404 and 500 pages
- Static asset structure ready for deployment

## Included features

- Public marketing pages: home, services, pricing, policies, contact
- Client registration and login
- Service request intake
- Client dashboard for orders, tickets, and billing
- Support ticket system with severity, category, support mode, and hourly billing
- Ticket messaging thread
- Billable time tracking for support work
- Break-even and recommended quote logic for jobs
- Admin dashboard for pricing, orders, tickets, and payments
- Stripe Checkout scaffold with webhook handler

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demo admin

```bash
flask --app run.py seed-demo
```

Demo login:

- Email: `admin@neonroo.local`
- Password: `ChangeMe123!`

Change that immediately.

## Production run

Set `.env` to production values, then run with Gunicorn:

```bash
cp .env.example .env
# edit the values first

gunicorn -c gunicorn.conf.py wsgi:app
```

Recommended:

- Put Gunicorn behind Nginx or Caddy
- Use PostgreSQL instead of SQLite
- Use HTTPS only
- Rotate a strong `SECRET_KEY`
- Set real Stripe keys and webhook secret

## Nginx

A sample config is included at:

```text
deploy/nginx/neon_roo_computers.conf
```

## Docker

```bash
docker build -t neon-roo-computers .
docker run --env-file .env -p 8000:8000 neon-roo-computers
```

## Stripe setup

Add these to `.env`:

```env
STRIPE_SECRET_KEY=sk_live_or_test_...
STRIPE_PUBLIC_KEY=pk_live_or_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
BASE_URL=https://computers.neonroo.xyz
```

Webhook endpoint:

```text
https://computers.neonroo.xyz/billing/webhook
```

Recommended event:

- `checkout.session.completed`

## Still recommended before taking real customers

- Move to PostgreSQL
- Add CSRF protection across forms
- Add password reset and email verification
- Add email notifications for ticket replies and status changes
- Add file uploads for intake photos and invoices
- Add audit logs for admin actions
- Review all policies with a lawyer for your jurisdiction
