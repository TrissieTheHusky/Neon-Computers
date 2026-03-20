from datetime import UTC, datetime

import stripe
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..models import PaymentRequest

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')


def stripe_enabled() -> bool:
    return bool(current_app.config.get('STRIPE_SECRET_KEY'))


@billing_bp.route('/payments/<int:payment_id>')
@login_required
def payment_detail(payment_id: int):
    payment = PaymentRequest.query.get_or_404(payment_id)
    if payment.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('client.dashboard'))
    return render_template('client/payment_detail.html', payment=payment, stripe_enabled=stripe_enabled())


@billing_bp.route('/payments/<int:payment_id>/checkout', methods=['POST'])
@login_required
def create_checkout(payment_id: int):
    payment = PaymentRequest.query.get_or_404(payment_id)
    if payment.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('client.dashboard'))
    if payment.status == 'paid':
        flash('This payment request has already been paid.', 'info')
        return redirect(url_for('billing.payment_detail', payment_id=payment.id))
    if not stripe_enabled():
        flash('Stripe is not configured yet. You can still mark payments manually from the admin dashboard.', 'warning')
        return redirect(url_for('billing.payment_detail', payment_id=payment.id))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    session = stripe.checkout.Session.create(
        mode='payment',
        success_url=f"{current_app.config['BASE_URL']}{url_for('billing.checkout_success')}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{current_app.config['BASE_URL']}{url_for('billing.payment_detail', payment_id=payment.id)}",
        client_reference_id=payment.public_id,
        customer_email=current_user.email,
        line_items=[{
            'price_data': {
                'currency': payment.currency,
                'product_data': {'name': payment.description},
                'unit_amount': payment.amount_cents,
            },
            'quantity': 1,
        }],
        metadata={'payment_request_id': str(payment.id), 'public_id': payment.public_id},
    )
    payment.stripe_checkout_session_id = session.id
    db.session.commit()
    return redirect(session.url, code=303)


@billing_bp.route('/success')
@login_required
def checkout_success():
    session_id = request.args.get('session_id', '')
    payment = None
    if stripe_enabled() and session_id:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        session = stripe.checkout.Session.retrieve(session_id)
        payment = PaymentRequest.query.filter_by(stripe_checkout_session_id=session.id).first()
        if payment and session.payment_status == 'paid' and payment.status != 'paid':
            payment.status = 'paid'
            payment.paid_at = datetime.now(UTC)
            payment.stripe_payment_intent_id = session.payment_intent
            db.session.commit()
    return render_template('client/checkout_success.html', payment=payment)


@billing_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    if not stripe_enabled() or not current_app.config.get('STRIPE_WEBHOOK_SECRET'):
        return {'ok': False, 'error': 'stripe_not_configured'}, 400

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET'])
    except Exception:
        return {'ok': False, 'error': 'invalid_signature'}, 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        payment = PaymentRequest.query.filter_by(stripe_checkout_session_id=session.get('id')).first()
        if payment:
            payment.status = 'paid'
            payment.paid_at = datetime.now(UTC)
            payment.stripe_payment_intent_id = session.get('payment_intent')
            db.session.commit()

    return {'ok': True}
