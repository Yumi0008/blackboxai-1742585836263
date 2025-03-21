from flask import render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
from . import inventory_bp
from .models import InventoryItem, InventoryTransaction, InventoryKOT, InventoryKOTItem
from app import db
from logger import get_module_logger

# Initialize logger for inventory module
logger = get_module_logger(__name__)

@inventory_bp.route('/')
def index():
    """Inventory module index page"""
    # Get inventory statistics
    total_items = InventoryItem.query.count()
    low_stock_items = InventoryItem.query.filter_by(status='low_stock').count()
    out_of_stock_items = InventoryItem.query.filter_by(status='out_of_stock').count()
    
    # Get recent transactions
    recent_transactions = InventoryTransaction.query.order_by(
        InventoryTransaction.created_at.desc()
    ).limit(5).all()
    
    # Get pending KOTs
    pending_kots = InventoryKOT.query.filter_by(status='pending').count()
    
    stats = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'pending_kots': pending_kots
    }
    
    return render_template('inventory/index.html', 
                         stats=stats,
                         recent_transactions=recent_transactions)

@inventory_bp.route('/kot', methods=['GET', 'POST'])
def kot():
    """Handle inventory KOT generation"""
    if request.method == 'POST':
        try:
            # Extract form data
            data = request.form
            
            # Create new KOT
            kot = InventoryKOT(
                kot_number=f"IKOT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                priority=data.get('priority', 'normal'),
                requested_by=data.get('requested_by'),
                notes=data.get('notes')
            )
            
            # Add KOT items
            items = request.form.getlist('items[]')
            quantities = request.form.getlist('quantities[]')
            
            for item_id, qty in zip(items, quantities):
                kot_item = InventoryKOTItem(
                    item_id=int(item_id),
                    quantity_requested=float(qty)
                )
                kot.items.append(kot_item)
            
            # Save to database
            db.session.add(kot)
            db.session.commit()
            
            logger.info(f"Created new Inventory KOT: {kot.kot_number}")
            flash('Inventory KOT generated successfully!', 'success')
            
            return redirect(url_for('inventory.kot_details', kot_id=kot.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating Inventory KOT: {str(e)}")
            flash('Error generating Inventory KOT. Please try again.', 'danger')
            return redirect(url_for('inventory.kot'))
    
    # GET request - show KOT form
    items = InventoryItem.query.filter_by(status='active').all()
    return render_template('inventory/kot_form.html', items=items)

@inventory_bp.route('/kot/<int:kot_id>')
def kot_details(kot_id):
    """Display KOT details"""
    kot = InventoryKOT.query.get_or_404(kot_id)
    return render_template('inventory/kot_details.html', kot=kot)

@inventory_bp.route('/kot/approve', methods=['POST'])
def approve_kot():
    """Approve inventory KOT"""
    try:
        kot_id = request.form.get('kot_id')
        approved_quantities = request.form.getlist('approved_quantities[]')
        
        kot = InventoryKOT.query.get_or_404(kot_id)
        
        # Update KOT status and items
        kot.status = 'approved'
        kot.approved_by = request.form.get('approved_by')
        
        for item, qty in zip(kot.items, approved_quantities):
            item.quantity_approved = float(qty)
            item.status = 'approved'
            
            # Create inventory transaction
            transaction = InventoryTransaction(
                item_id=item.item_id,
                transaction_type='out',
                quantity=float(qty),
                reference_number=kot.kot_number,
                created_by=kot.approved_by
            )
            
            # Update item stock
            inventory_item = InventoryItem.query.get(item.item_id)
            inventory_item.current_stock -= float(qty)
            inventory_item.update_status()
            
            db.session.add(transaction)
        
        db.session.commit()
        logger.info(f"Approved Inventory KOT: {kot.kot_number}")
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving Inventory KOT: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/track')
def track():
    """Inventory tracking page"""
    # Get filter parameters
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search')
    
    # Build query
    query = InventoryItem.query
    
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(InventoryItem.name.ilike(f'%{search}%'))
    
    items = query.order_by(InventoryItem.name).all()
    
    # Get unique categories for filter dropdown
    categories = db.session.query(InventoryItem.category).distinct().all()
    
    return render_template('inventory/track.html', 
                         items=items,
                         categories=categories)

@inventory_bp.route('/api/items')
def get_items():
    """API endpoint to get inventory items"""
    try:
        items = InventoryItem.query.all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        logger.error(f"Error fetching inventory items: {str(e)}")
        return jsonify({'error': str(e)}), 400

@inventory_bp.route('/api/transactions')
def get_transactions():
    """API endpoint to get inventory transactions"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        item_id = request.args.get('item_id')
        
        query = InventoryTransaction.query
        
        if start_date and end_date:
            query = query.filter(
                InventoryTransaction.created_at.between(start_date, end_date)
            )
        
        if item_id:
            query = query.filter_by(item_id=item_id)
            
        transactions = query.order_by(
            InventoryTransaction.created_at.desc()
        ).all()
        
        return jsonify([txn.to_dict() for txn in transactions])
        
    except Exception as e:
        logger.error(f"Error fetching inventory transactions: {str(e)}")
        return jsonify({'error': str(e)}), 400

@inventory_bp.route('/api/kots')
def get_kots():
    """API endpoint to get inventory KOTs"""
    try:
        status = request.args.get('status')
        
        query = InventoryKOT.query
        
        if status:
            query = query.filter_by(status=status)
            
        kots = query.order_by(InventoryKOT.created_at.desc()).all()
        
        return jsonify([kot.to_dict() for kot in kots])
        
    except Exception as e:
        logger.error(f"Error fetching inventory KOTs: {str(e)}")
        return jsonify({'error': str(e)}), 400