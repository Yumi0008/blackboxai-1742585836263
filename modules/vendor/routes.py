from flask import render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
from . import vendor_bp
from .models import Vendor, VendorOrder, VendorOrderItem, VendorPayment
from modules.inventory.models import InventoryItem, InventoryTransaction
from app import db
from logger import get_module_logger

# Initialize logger for vendor module
logger = get_module_logger(__name__)

@vendor_bp.route('/')
def index():
    """Vendor module index page"""
    # Get vendor statistics
    total_vendors = Vendor.query.count()
    active_vendors = Vendor.query.filter_by(status='active').count()
    pending_orders = VendorOrder.query.filter_by(status='placed').count()
    pending_payments = VendorOrder.query.filter_by(payment_status='pending').count()
    
    # Get recent orders
    recent_orders = VendorOrder.query.order_by(
        VendorOrder.created_at.desc()
    ).limit(5).all()
    
    stats = {
        'total_vendors': total_vendors,
        'active_vendors': active_vendors,
        'pending_orders': pending_orders,
        'pending_payments': pending_payments
    }
    
    return render_template('vendor/index.html',
                         stats=stats,
                         recent_orders=recent_orders)

@vendor_bp.route('/vendors')
def vendors():
    """List all vendors"""
    vendors = Vendor.query.order_by(Vendor.name).all()
    return render_template('vendor/vendors.html', vendors=vendors)

@vendor_bp.route('/vendors/add', methods=['GET', 'POST'])
def add_vendor():
    """Add new vendor"""
    if request.method == 'POST':
        try:
            vendor = Vendor(
                name=request.form['name'],
                contact_person=request.form['contact_person'],
                email=request.form['email'],
                phone=request.form['phone'],
                address=request.form['address'],
                gst_number=request.form['gst_number'],
                payment_terms=request.form['payment_terms'],
                notes=request.form['notes']
            )
            
            db.session.add(vendor)
            db.session.commit()
            
            logger.info(f"Added new vendor: {vendor.name}")
            flash('Vendor added successfully!', 'success')
            return redirect(url_for('vendor.vendors'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding vendor: {str(e)}")
            flash('Error adding vendor. Please try again.', 'danger')
            return redirect(url_for('vendor.add_vendor'))
    
    return render_template('vendor/vendor_form.html')

@vendor_bp.route('/vendors/<int:vendor_id>')
def vendor_details(vendor_id):
    """View vendor details"""
    vendor = Vendor.query.get_or_404(vendor_id)
    return render_template('vendor/vendor_details.html', vendor=vendor)

@vendor_bp.route('/orders')
def orders():
    """List all orders"""
    orders = VendorOrder.query.order_by(VendorOrder.created_at.desc()).all()
    return render_template('vendor/orders.html', orders=orders)

@vendor_bp.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    """Add new vendor order"""
    if request.method == 'POST':
        try:
            # Create new order
            order = VendorOrder(
                order_number=f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                vendor_id=request.form['vendor_id'],
                expected_delivery_date=datetime.strptime(
                    request.form['expected_delivery_date'], '%Y-%m-%d'
                ) if request.form['expected_delivery_date'] else None,
                notes=request.form['notes']
            )
            
            # Add order items
            items = request.form.getlist('items[]')
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            for item_id, qty, price in zip(items, quantities, prices):
                order_item = VendorOrderItem(
                    item_id=int(item_id),
                    quantity=float(qty),
                    unit_price=float(price)
                )
                order_item.calculate_total()
                order.items.append(order_item)
            
            order.calculate_total()
            
            db.session.add(order)
            db.session.commit()
            
            logger.info(f"Created new vendor order: {order.order_number}")
            flash('Order created successfully!', 'success')
            return redirect(url_for('vendor.order_details', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating order: {str(e)}")
            flash('Error creating order. Please try again.', 'danger')
            return redirect(url_for('vendor.add_order'))
    
    vendors = Vendor.query.filter_by(status='active').all()
    items = InventoryItem.query.all()
    return render_template('vendor/order_form.html',
                         vendors=vendors,
                         items=items)

@vendor_bp.route('/orders/<int:order_id>')
def order_details(order_id):
    """View order details"""
    order = VendorOrder.query.get_or_404(order_id)
    return render_template('vendor/order_details.html', order=order)

@vendor_bp.route('/orders/<int:order_id>/receive', methods=['POST'])
def receive_order(order_id):
    """Mark order as received and update inventory"""
    try:
        order = VendorOrder.query.get_or_404(order_id)
        received_quantities = request.form.getlist('received_quantities[]')
        
        # Update order status and received quantities
        order.status = 'received'
        order.delivery_date = datetime.utcnow()
        
        for item, qty in zip(order.items, received_quantities):
            qty = float(qty)
            item.received_quantity = qty
            
            # Create inventory transaction
            transaction = InventoryTransaction(
                item_id=item.item_id,
                transaction_type='in',
                quantity=qty,
                unit_price=item.unit_price,
                total_price=qty * item.unit_price,
                reference_number=order.order_number,
                notes=f"Received from vendor order {order.order_number}"
            )
            
            # Update inventory item stock
            inventory_item = item.item
            inventory_item.current_stock += qty
            inventory_item.update_status()
            
            db.session.add(transaction)
        
        db.session.commit()
        logger.info(f"Received vendor order: {order.order_number}")
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error receiving order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@vendor_bp.route('/payments')
def payments():
    """List all payments"""
    payments = VendorPayment.query.order_by(VendorPayment.created_at.desc()).all()
    return render_template('vendor/payments.html', payments=payments)

@vendor_bp.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    """Add new vendor payment"""
    if request.method == 'POST':
        try:
            payment = VendorPayment(
                vendor_id=request.form['vendor_id'],
                order_id=request.form['order_id'],
                payment_number=f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                payment_date=datetime.strptime(
                    request.form['payment_date'], '%Y-%m-%d'
                ),
                amount=float(request.form['amount']),
                payment_method=request.form['payment_method'],
                reference_number=request.form['reference_number'],
                notes=request.form['notes']
            )
            
            db.session.add(payment)
            
            # Update order payment status
            order = payment.order
            order.payments.append(payment)
            order.update_payment_status()
            
            db.session.commit()
            
            logger.info(f"Added new payment: {payment.payment_number}")
            flash('Payment added successfully!', 'success')
            return redirect(url_for('vendor.payments'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding payment: {str(e)}")
            flash('Error adding payment. Please try again.', 'danger')
            return redirect(url_for('vendor.add_payment'))
    
    vendors = Vendor.query.all()
    orders = VendorOrder.query.filter(
        VendorOrder.payment_status.in_(['pending', 'partial'])
    ).all()
    
    return render_template('vendor/payment_form.html',
                         vendors=vendors,
                         orders=orders)

@vendor_bp.route('/api/vendors')
def get_vendors():
    """API endpoint to get vendors"""
    try:
        vendors = Vendor.query.all()
        return jsonify([vendor.to_dict() for vendor in vendors])
    except Exception as e:
        logger.error(f"Error fetching vendors: {str(e)}")
        return jsonify({'error': str(e)}), 400

@vendor_bp.route('/api/orders')
def get_orders():
    """API endpoint to get orders"""
    try:
        vendor_id = request.args.get('vendor_id')
        status = request.args.get('status')
        
        query = VendorOrder.query
        
        if vendor_id:
            query = query.filter_by(vendor_id=vendor_id)
        if status:
            query = query.filter_by(status=status)
            
        orders = query.order_by(VendorOrder.created_at.desc()).all()
        
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({'error': str(e)}), 400

@vendor_bp.route('/api/payments')
def get_payments():
    """API endpoint to get payments"""
    try:
        vendor_id = request.args.get('vendor_id')
        order_id = request.args.get('order_id')
        
        query = VendorPayment.query
        
        if vendor_id:
            query = query.filter_by(vendor_id=vendor_id)
        if order_id:
            query = query.filter_by(order_id=order_id)
            
        payments = query.order_by(VendorPayment.created_at.desc()).all()
        
        return jsonify([payment.to_dict() for payment in payments])
    except Exception as e:
        logger.error(f"Error fetching payments: {str(e)}")
        return jsonify({'error': str(e)}), 400