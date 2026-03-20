import random
import string

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..models import CompanySettings, Order, OrderUpdate

main_bp = Blueprint('main', __name__)


def generate_public_id(prefix: str) -> str:
    return f"{prefix}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@main_bp.route('/')
def index():
    settings = CompanySettings.query.first()
    return render_template('main/index.html', settings=settings)


@main_bp.route('/services')
def services():
    settings = CompanySettings.query.first()
    return render_template('main/services.html', settings=settings)


@main_bp.route('/pricing')
def pricing():
    settings = CompanySettings.query.first()
    return render_template('main/pricing.html', settings=settings)


@main_bp.route('/policies')
def policies():
    settings = CompanySettings.query.first()
    return render_template('policies/index.html', settings=settings)


@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html')


@main_bp.route('/request-service', methods=['GET', 'POST'])
@login_required
def request_service():
    settings = CompanySettings.query.first()

    if request.method == 'POST':
        service_type = request.form.get('service_type', 'Repair')
        priority = request.form.get('priority', 'Normal')
        labor_rate = settings.support_hourly_rate if settings else 95.0
        margin = settings.target_margin_percent if settings else 35.0
        if service_type == 'Custom Build':
            labor_rate = settings.pc_build_labor if settings else 175.0
        order = Order(
            public_id=generate_public_id('NRC'),
            user_id=current_user.id,
            service_type=service_type,
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip(),
            priority=priority,
            device_make=request.form.get('device_make', '').strip(),
            device_model=request.form.get('device_model', '').strip(),
            serial_number=request.form.get('serial_number', '').strip(),
            client_budget=float(request.form.get('client_budget') or 0),
            labor_rate=labor_rate,
            target_margin_percent=margin,
            deposit_required=(settings.intake_deposit if settings else 50.0),
        )
        if priority == 'Rush' and settings:
            order.labor_rate = round(order.labor_rate * settings.rush_multiplier, 2)
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderUpdate(order_id=order.id, note='Service request received and waiting for staff review.'))
        db.session.commit()
        flash('Your service request has been submitted.', 'success')
        return redirect(url_for('client.order_detail', order_id=order.id))

    return render_template('main/request_service.html', settings=settings)
