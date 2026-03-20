from datetime import datetime, UTC
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    orders = db.relationship('Order', backref='client', lazy=True)
    tickets = db.relationship('SupportTicket', backref='client', lazy=True)
    messages = db.relationship('TicketMessage', backref='author', lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class CompanySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(120), default='Neon Roo Computers & Upgrades')
    support_hourly_rate = db.Column(db.Float, default=95.00)
    remote_support_hourly_rate = db.Column(db.Float, default=85.00)
    emergency_support_hourly_rate = db.Column(db.Float, default=125.00)
    diagnostic_fee = db.Column(db.Float, default=45.00)
    pc_build_labor = db.Column(db.Float, default=175.00)
    hardware_install_labor = db.Column(db.Float, default=70.00)
    os_install_labor = db.Column(db.Float, default=110.00)
    data_transfer_labor = db.Column(db.Float, default=85.00)
    consultation_rate = db.Column(db.Float, default=65.00)
    rush_multiplier = db.Column(db.Float, default=1.35)
    target_margin_percent = db.Column(db.Float, default=35.00)
    intake_deposit = db.Column(db.Float, default=50.00)
    custom_build_deposit_percent = db.Column(db.Float, default=50.00)
    payment_terms_days = db.Column(db.Integer, default=7)
    sales_tax_note = db.Column(db.String(255), default='Sales tax may apply where required.')
    support_billing_note = db.Column(db.String(255), default='Remote and on-site support are billed in actual time spent, rounded to the nearest 15 minutes.')
    warranty_note = db.Column(db.String(255), default='Labor warranty limited to workmanship; manufacturer defects are handled through the applicable vendor or manufacturer when available.')


class Order(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Received', nullable=False)
    priority = db.Column(db.String(30), default='Normal', nullable=False)
    quoted_price = db.Column(db.Float, default=0.0)
    deposit_required = db.Column(db.Float, default=0.0)
    parts_cost = db.Column(db.Float, default=0.0)
    labor_hours = db.Column(db.Float, default=0.0)
    labor_rate = db.Column(db.Float, default=0.0)
    target_margin_percent = db.Column(db.Float, default=0.0)
    device_make = db.Column(db.String(100))
    device_model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    client_budget = db.Column(db.Float, default=0.0)

    updates = db.relationship('OrderUpdate', backref='order', lazy=True, cascade='all, delete-orphan', order_by='OrderUpdate.created_at.desc()')
    payment_requests = db.relationship('PaymentRequest', backref='order', lazy=True, cascade='all, delete-orphan')

    @property
    def effective_labor_rate(self):
        if self.labor_rate and self.labor_rate > 0:
            return self.labor_rate
        settings = CompanySettings.query.first()
        return settings.support_hourly_rate if settings else 95.0

    @property
    def estimated_break_even(self):
        return round((self.parts_cost or 0) + ((self.labor_hours or 0) * self.effective_labor_rate), 2)

    @property
    def recommended_quote(self):
        margin = self.target_margin_percent or (CompanySettings.query.first().target_margin_percent if CompanySettings.query.first() else 35.0)
        return round(self.estimated_break_even * (1 + (margin / 100)), 2)

    @property
    def total_paid(self):
        return round(sum(p.amount for p in self.payment_requests if p.status == 'paid'), 2)

    @property
    def balance_due(self):
        total = self.quoted_price or self.recommended_quote
        return round(max(total - self.total_paid, 0), 2)


class OrderUpdate(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    visible_to_client = db.Column(db.Boolean, default=True, nullable=False)


class SupportTicket(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    support_mode = db.Column(db.String(30), default='Remote', nullable=False)
    issue_summary = db.Column(db.Text, nullable=False)
    what_happened = db.Column(db.Text, nullable=False)
    troubleshooting_done = db.Column(db.Text)
    device_type = db.Column(db.String(50))
    operating_system = db.Column(db.String(50))
    preferred_contact = db.Column(db.String(30), default='Portal')
    status = db.Column(db.String(50), default='Open', nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0)

    messages = db.relationship('TicketMessage', backref='ticket', lazy=True, cascade='all, delete-orphan', order_by='TicketMessage.created_at.asc()')
    time_entries = db.relationship('TimeEntry', backref='ticket', lazy=True, cascade='all, delete-orphan', order_by='TimeEntry.created_at.desc()')
    payment_requests = db.relationship('PaymentRequest', backref='ticket', lazy=True, cascade='all, delete-orphan')

    @property
    def billable_total(self):
        return round(sum(entry.hours * entry.rate for entry in self.time_entries), 2)

    @property
    def total_paid(self):
        return round(sum(p.amount for p in self.payment_requests if p.status == 'paid'), 2)

    @property
    def balance_due(self):
        return round(max(self.billable_total - self.total_paid, 0), 2)


class TicketMessage(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sender_name = db.Column(db.String(120), nullable=False)
    is_staff = db.Column(db.Boolean, default=False, nullable=False)
    body = db.Column(db.Text, nullable=False)


class TimeEntry(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    billable = db.Column(db.Boolean, default=True, nullable=False)


class PaymentRequest(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(24), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'))
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='usd', nullable=False)
    status = db.Column(db.String(30), default='open', nullable=False)
    due_date = db.Column(db.DateTime)
    stripe_checkout_session_id = db.Column(db.String(255))
    stripe_payment_intent_id = db.Column(db.String(255))
    paid_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='payment_requests')

    @property
    def amount_cents(self) -> int:
        return int(Decimal(str(self.amount)) * 100)
