from datetime import datetime
from app import db

class Vendor(db.Model):
    """Model for vendors"""
    __tablename__ = 'vendors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    gst_number = db.Column(db.String(20))
    payment_terms = db.Column(db.String(100))  # e.g., "Net 30", "COD"
    status = db.Column(db.String(20), default='active')  # active, inactive
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship('VendorOrder', backref='vendor', lazy=True)
    payments = db.relationship('VendorPayment', backref='vendor', lazy=True)

    def __repr__(self):
        return f'<Vendor {self.name}>'

    def to_dict(self):
        """Convert vendor to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'gst_number': self.gst_number,
            'payment_terms': self.payment_terms,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class VendorOrder(db.Model):
    """Model for vendor orders"""
    __tablename__ = 'vendor_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.DateTime)
    delivery_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')  # draft, placed, confirmed, received, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, paid
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('VendorOrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('VendorPayment', backref='order', lazy=True)

    def __repr__(self):
        return f'<VendorOrder {self.order_number}>'

    def calculate_total(self):
        """Calculate total order amount"""
        self.total_amount = sum(item.total_price for item in self.items)

    def update_payment_status(self):
        """Update payment status based on payments received"""
        total_paid = sum(payment.amount for payment in self.payments)
        if total_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif total_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'

    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'vendor_id': self.vendor_id,
            'order_date': self.order_date.isoformat(),
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class VendorOrderItem(db.Model):
    """Model for items in vendor orders"""
    __tablename__ = 'vendor_order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('vendor_orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    received_quantity = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with inventory item
    item = db.relationship('InventoryItem')

    def __repr__(self):
        return f'<VendorOrderItem {self.id}>'

    def calculate_total(self):
        """Calculate total price for the item"""
        self.total_price = self.quantity * self.unit_price

    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'item_id': self.item_id,
            'item_name': self.item.name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'received_quantity': self.received_quantity,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class VendorPayment(db.Model):
    """Model for vendor payments"""
    __tablename__ = 'vendor_payments'

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('vendor_orders.id'), nullable=False)
    payment_number = db.Column(db.String(20), unique=True, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, cheque
    reference_number = db.Column(db.String(50))  # cheque number, transaction ID, etc.
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='completed')  # completed, pending, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<VendorPayment {self.payment_number}>'

    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'vendor_id': self.vendor_id,
            'order_id': self.order_id,
            'payment_number': self.payment_number,
            'payment_date': self.payment_date.isoformat(),
            'amount': self.amount,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }