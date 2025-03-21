from datetime import datetime
from app import db

class BillingOrder(db.Model):
    """Model for restaurant billing orders"""
    __tablename__ = 'billing_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    table_number = db.Column(db.String(10))
    customer_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, preparing, completed, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, partially_paid
    payment_method = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with order items
    items = db.relationship('BillingOrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<BillingOrder {self.order_number}>'

    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'table_number': self.table_number,
            'customer_name': self.customer_name,
            'status': self.status,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class BillingOrderItem(db.Model):
    """Model for individual items in a billing order"""
    __tablename__ = 'billing_order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('billing_orders.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, preparing, served, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BillingOrderItem {self.item_name}>'

    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class KOTOrder(db.Model):
    """Model for Kitchen Order Tickets"""
    __tablename__ = 'kot_orders'

    id = db.Column(db.Integer, primary_key=True)
    kot_number = db.Column(db.String(20), unique=True, nullable=False)
    billing_order_id = db.Column(db.Integer, db.ForeignKey('billing_orders.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(10), default='normal')  # low, normal, high
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with billing order
    billing_order = db.relationship('BillingOrder', backref='kot_orders', lazy=True)
    
    def __repr__(self):
        return f'<KOTOrder {self.kot_number}>'

    def to_dict(self):
        """Convert KOT order to dictionary"""
        return {
            'id': self.id,
            'kot_number': self.kot_number,
            'billing_order_id': self.billing_order_id,
            'status': self.status,
            'priority': self.priority,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }