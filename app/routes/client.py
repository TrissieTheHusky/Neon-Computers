import random
import string

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..models import CompanySettings, Order, PaymentRequest, SupportTicket, TicketMessage

client_bp = Blueprint('client', __name__, url_prefix='/client')


def generate_public_id(prefix: str) -> str:
    return f"{prefix}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@client_bp.route('/dashboard')
@login_required
def dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
    payments = PaymentRequest.query.filter_by(user_id=current_user.id).order_by(PaymentRequest.created_at.desc()).all()
    return render_template('client/dashboard.html', orders=orders, tickets=tickets, payments=payments)


@client_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id: int):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('client/order_detail.html', order=order)


@client_bp.route('/support/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    settings = CompanySettings.query.first()

    if request.method == 'POST':
        support_mode = request.form.get('support_mode', 'Remote')
        severity = request.form.get('severity', 'Standard')
        hourly_rate = settings.remote_support_hourly_rate if support_mode == 'Remote' else settings.support_hourly_rate
        if severity == 'Emergency':
            hourly_rate = settings.emergency_support_hourly_rate
        ticket = SupportTicket(
            public_id=generate_public_id('TKT'),
            user_id=current_user.id,
            subject=request.form.get('subject', '').strip(),
            category=request.form.get('category', '').strip(),
            severity=severity,
            support_mode=support_mode,
            issue_summary=request.form.get('issue_summary', '').strip(),
            what_happened=request.form.get('what_happened', '').strip(),
            troubleshooting_done=request.form.get('troubleshooting_done', '').strip(),
            device_type=request.form.get('device_type', '').strip(),
            operating_system=request.form.get('operating_system', '').strip(),
            preferred_contact=request.form.get('preferred_contact', 'Portal').strip(),
            hourly_rate=hourly_rate,
        )
        db.session.add(ticket)
        db.session.flush()
        db.session.add(TicketMessage(
            ticket_id=ticket.id,
            user_id=current_user.id,
            sender_name=current_user.full_name,
            is_staff=False,
            body='Ticket created. Initial issue details were submitted by the client.',
        ))
        db.session.commit()
        flash('Support ticket created.', 'success')
        return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))

    return render_template('client/new_ticket.html', settings=settings)


@client_bp.route('/support/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id: int):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if body:
            db.session.add(TicketMessage(
                ticket_id=ticket.id,
                user_id=current_user.id,
                sender_name=current_user.full_name,
                is_staff=False,
                body=body,
            ))
            db.session.commit()
            flash('Message sent.', 'success')
        return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))

    return render_template('client/ticket_detail.html', ticket=ticket)
