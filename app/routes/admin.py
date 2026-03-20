import random
import string
from datetime import UTC, datetime, timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..models import CompanySettings, Order, OrderUpdate, PaymentRequest, SupportTicket, TicketMessage, TimeEntry

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


def generate_public_id(prefix: str) -> str:
    return f"{prefix}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


@admin_bp.route('/')
@login_required
def dashboard():
    require_admin()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    payments = PaymentRequest.query.order_by(PaymentRequest.created_at.desc()).all()
    settings = CompanySettings.query.first()
    return render_template('admin/dashboard.html', orders=orders, tickets=tickets, payments=payments, settings=settings)


@admin_bp.route('/orders/<int:order_id>', methods=['POST'])
@login_required
def update_order(order_id: int):
    require_admin()
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status', order.status)
    order.quoted_price = float(request.form.get('quoted_price') or order.quoted_price or 0)
    order.parts_cost = float(request.form.get('parts_cost') or order.parts_cost or 0)
    order.labor_hours = float(request.form.get('labor_hours') or order.labor_hours or 0)
    order.labor_rate = float(request.form.get('labor_rate') or order.labor_rate or 0)
    order.deposit_required = float(request.form.get('deposit_required') or order.deposit_required or 0)
    order.target_margin_percent = float(request.form.get('target_margin_percent') or order.target_margin_percent or 0)
    note = request.form.get('note', '').strip()
    visible_to_client = bool(request.form.get('visible_to_client'))
    if note:
        db.session.add(OrderUpdate(order_id=order.id, note=note, visible_to_client=visible_to_client))
    db.session.commit()
    flash('Order updated.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/orders/<int:order_id>/payment', methods=['POST'])
@login_required
def create_order_payment(order_id: int):
    require_admin()
    order = Order.query.get_or_404(order_id)
    settings = CompanySettings.query.first()
    amount = float(request.form.get('amount') or 0)
    description = request.form.get('description', '').strip() or f'Payment for order {order.public_id}'
    if amount <= 0:
        flash('Payment request amount must be greater than zero.', 'danger')
        return redirect(url_for('admin.dashboard'))
    payment = PaymentRequest(
        public_id=generate_public_id('PAY'),
        user_id=order.user_id,
        order_id=order.id,
        description=description,
        amount=amount,
        due_date=datetime.now(UTC) + timedelta(days=(settings.payment_terms_days if settings else 7)),
    )
    db.session.add(payment)
    db.session.commit()
    flash('Order payment request created.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/tickets/<int:ticket_id>/message', methods=['POST'])
@login_required
def message_ticket(ticket_id: int):
    require_admin()
    ticket = SupportTicket.query.get_or_404(ticket_id)
    body = request.form.get('body', '').strip()
    status = request.form.get('status', ticket.status)
    ticket.status = status
    if body:
        db.session.add(TicketMessage(ticket_id=ticket.id, sender_name=current_app.config['COMPANY_NAME'], is_staff=True, body=body))
    db.session.commit()
    flash('Ticket updated.', 'success')
    return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))


@admin_bp.route('/tickets/<int:ticket_id>/time', methods=['POST'])
@login_required
def add_time(ticket_id: int):
    require_admin()
    ticket = SupportTicket.query.get_or_404(ticket_id)
    description = request.form.get('description', '').strip()
    hours = float(request.form.get('hours') or 0)
    rate = float(request.form.get('rate') or ticket.hourly_rate or 0)
    if description and hours > 0:
        db.session.add(TimeEntry(ticket_id=ticket.id, description=description, hours=hours, rate=rate, billable=True))
        db.session.commit()
        flash('Time entry added.', 'success')
    else:
        flash('Description and positive hours are required.', 'danger')
    return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))


@admin_bp.route('/tickets/<int:ticket_id>/payment', methods=['POST'])
@login_required
def create_ticket_payment(ticket_id: int):
    require_admin()
    ticket = SupportTicket.query.get_or_404(ticket_id)
    settings = CompanySettings.query.first()
    amount = float(request.form.get('amount') or ticket.balance_due or 0)
    description = request.form.get('description', '').strip() or f'Support charges for ticket {ticket.public_id}'
    if amount <= 0:
        flash('Payment request amount must be greater than zero.', 'danger')
        return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))
    payment = PaymentRequest(
        public_id=generate_public_id('PAY'),
        user_id=ticket.user_id,
        ticket_id=ticket.id,
        description=description,
        amount=amount,
        due_date=datetime.now(UTC) + timedelta(days=(settings.payment_terms_days if settings else 7)),
    )
    db.session.add(payment)
    db.session.commit()
    flash('Support payment request created.', 'success')
    return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))


@admin_bp.route('/payments/<int:payment_id>/mark-paid', methods=['POST'])
@login_required
def mark_payment_paid(payment_id: int):
    require_admin()
    payment = PaymentRequest.query.get_or_404(payment_id)
    payment.status = 'paid'
    payment.paid_at = datetime.now(UTC)
    db.session.commit()
    flash('Payment marked as paid.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/settings', methods=['POST'])
@login_required
def update_settings():
    require_admin()
    settings = CompanySettings.query.first()
    fields = [
        'support_hourly_rate', 'remote_support_hourly_rate', 'emergency_support_hourly_rate', 'diagnostic_fee',
        'pc_build_labor', 'hardware_install_labor', 'os_install_labor', 'data_transfer_labor', 'consultation_rate',
        'rush_multiplier', 'target_margin_percent', 'intake_deposit', 'custom_build_deposit_percent'
    ]
    for field in fields:
        setattr(settings, field, float(request.form.get(field) or getattr(settings, field)))
    settings.payment_terms_days = int(request.form.get('payment_terms_days') or settings.payment_terms_days)
    settings.sales_tax_note = request.form.get('sales_tax_note', settings.sales_tax_note)
    settings.support_billing_note = request.form.get('support_billing_note', settings.support_billing_note)
    settings.warranty_note = request.form.get('warranty_note', settings.warranty_note)
    db.session.commit()
    flash('Settings updated.', 'success')
    return redirect(url_for('admin.dashboard'))
