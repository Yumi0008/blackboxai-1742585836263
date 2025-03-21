from flask import render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
from . import billing_bp
from .models import BillingOrder, BillingOrderItem, KOTOrder
from app import db
from logger import get_module_logger

# Initialize logger for billing module
logger = get_module_logger(__name__)

@billing_bp.route('/')
def index():
    """Billing module index page"""
    return render_template('billing/index.html')

@billing_bp.route('/kot', methods=['GET', 'POST'])
def kot():
    """Handle KOT generation"""
    if request.method == 'POST':
        try:
            # Extract form data
            data = request.form
            
            # Create new billing order
            order = BillingOrder(
                order_number=f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                table_number=data.get('table_number'),
                customer_name=data.get('customer_name'),
                notes=data.get('notes')
            )
            
            # Add order items
            items = request.form.getlist('items[]')
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            total_amount = 0
            for item, qty, price in zip(items, quantities, prices):
                qty = int(qty)
                price = float(price)
                total = qty * price
                total_amount += total
                
                order_item = BillingOrderItem(
                    item_name=item,
                    quantity=qty,
                    unit_price=price,
                    total_price=total
                )
                order.items.append(order_item)
            
            order.total_amount = total_amount
            
            # Create KOT
            kot = KOTOrder(
                kot_number=f"KOT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                billing_order=order,
                priority=data.get('priority', 'normal')
            )
            
            # Save to database
            db.session.add(order)
            db.session.add(kot)
            db.session.commit()
            
            logger.info(f"Created new KOT: {kot.kot_number} for order: {order.order_number}")
            flash('KOT generated successfully!', 'success')
            
            # Return KOT details for printing
            return render_template('billing/kot_print.html', order=order, kot=kot)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating KOT: {str(e)}")
            flash('Error generating KOT. Please try again.', 'danger')
            return redirect(url_for('billing.kot'))
    
    return render_template('billing/kot_form.html')

@billing_bp.route('/kitchen')
def kitchen():
    """Kitchen display system"""
    # Get pending and in-progress KOTs
    active_kots = KOTOrder.query.filter(
        KOTOrder.status.in_(['pending', 'in_progress'])
    ).order_by(
        KOTOrder.priority.desc(),
        KOTOrder.created_at.asc()
    ).all()
    
    return render_template('billing/kitchen_display.html', kots=active_kots)

@billing_bp.route('/kitchen/update_status', methods=['POST'])
def update_kot_status():
    """Update KOT status"""
    try:
        kot_id = request.form.get('kot_id')
        new_status = request.form.get('status')
        
        kot = KOTOrder.query.get_or_404(kot_id)
        kot.status = new_status
        db.session.commit()
        
        logger.info(f"Updated KOT {kot.kot_number} status to {new_status}")
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating KOT status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@billing_bp.route('/reports')
def reports():
    """Generate billing reports"""
    # Get date range from request
    start_date = request.args.get('start_date', 
                                 (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', 
                               datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Query orders within date range
    orders = BillingOrder.query.filter(
        BillingOrder.created_at.between(start_date, end_date)
    ).order_by(
        BillingOrder.created_at.desc()
    ).all()
    
    # Calculate statistics
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    completed_orders = sum(1 for order in orders if order.status == 'completed')
    cancelled_orders = sum(1 for order in orders if order.status == 'cancelled')
    
    stats = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render_template('billing/reports.html', orders=orders, stats=stats)

@billing_bp.route('/api/orders')
def get_orders():
    """API endpoint to get orders (for AJAX requests)"""
    try:
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = BillingOrder.query
        
        if status:
            query = query.filter_by(status=status)
            
        orders = query.order_by(BillingOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'total': orders.total,
            'pages': orders.pages,
            'current_page': orders.page
        })
        
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({'error': str(e)}), 400