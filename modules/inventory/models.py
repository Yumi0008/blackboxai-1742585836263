from datetime import datetime
from app import db

class InventoryItem(db.Model):
    """Model for inventory items"""
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # e.g., kg, liters, pieces
    current_stock = db.Column(db.Float, default=0.0)
    minimum_stock = db.Column(db.Float, default=0.0)
    maximum_stock = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, low_stock, out_of_stock
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('InventoryTransaction', backref='item', lazy=True)
    kot_items = db.relationship('InventoryKOTItem', backref='item', lazy=True)

    def __repr__(self):
        return f'<InventoryItem {self.name}>'

    def update_status(self):
        """Update item status based on current stock level"""
        if self.current_stock <= 0:
            self.status = 'out_of_stock'
        elif self.current_stock <= self.minimum_stock:
            self.status = 'low_stock'
        else:
            self.status = 'active'

    def to_dict(self):
        """Convert item to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'unit': self.unit,
            'current_stock': self.current_stock,
            'minimum_stock': self.minimum_stock,
            'maximum_stock': self.maximum_stock,
            'unit_price': self.unit_price,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class InventoryTransaction(db.Model):
    """Model for inventory transactions"""
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # in, out, adjustment
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float)
    total_price = db.Column(db.Float)
    reference_number = db.Column(db.String(50))  # PO number, KOT number, etc.
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type} {self.quantity}>'

    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'item_id': self.item_id,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class InventoryKOT(db.Model):
    """Model for inventory Kitchen Order Tickets"""
    __tablename__ = 'inventory_kots'

    id = db.Column(db.Integer, primary_key=True)
    kot_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    priority = db.Column(db.String(10), default='normal')  # low, normal, high
    requested_by = db.Column(db.String(100))
    approved_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('InventoryKOTItem', backref='kot', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<InventoryKOT {self.kot_number}>'

    def to_dict(self):
        """Convert KOT to dictionary"""
        return {
            'id': self.id,
            'kot_number': self.kot_number,
            'status': self.status,
            'priority': self.priority,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class InventoryKOTItem(db.Model):
    """Model for items in inventory KOT"""
    __tablename__ = 'inventory_kot_items'

    id = db.Column(db.Integer, primary_key=True)
    kot_id = db.Column(db.Integer, db.ForeignKey('inventory_kots.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    quantity_requested = db.Column(db.Float, nullable=False)
    quantity_approved = db.Column(db.Float)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryKOTItem {self.id}>'

    def to_dict(self):
        """Convert KOT item to dictionary"""
        return {
            'id': self.id,
            'kot_id': self.kot_id,
            'item_id': self.item_id,
            'quantity_requested': self.quantity_requested,
            'quantity_approved': self.quantity_approved,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }