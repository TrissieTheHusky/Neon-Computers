# Neon Roo Computers & Upgrades

A polished Flask starter for a computer repair, PC upgrade, custom build, and tech support business.

## Included

- Public marketing pages: home, services, pricing, policies, contact
- Client account registration and login
- Service request intake form
- Client dashboard for orders, tickets, and billing
- Support ticket intake with category, severity, device, operating system, and preferred contact method
- Ticket messaging thread
- Billable time tracking for support work
- Break-even and recommended quote logic for orders
- Admin dashboard for pricing, orders, tickets, and payments
- Stripe Checkout payment request scaffold with webhook handler

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open:

```bash
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

## Stripe setup

Add these to `.env`:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
BASE_URL=https://your-domain.example
```

Then register a webhook endpoint pointing to:

```text
https://your-domain.example/billing/webhook
```

Recommended event:

- `checkout.session.completed`

## Production cleanup

- Move from SQLite to PostgreSQL
- Put the app behind HTTPS
- Add email notifications
- Add file uploads for photos, invoices, and intake documents
- Add role-based audit logs
- Add password reset and email verification
- Replace placeholder contact details and policies
