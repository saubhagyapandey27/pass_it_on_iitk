from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Item, ItemImage, Wishlist
from app.forms import ItemForm, SearchForm
from app.utils import save_image
from werkzeug.utils import secure_filename
import os
from sqlalchemy import or_, and_

bp = Blueprint('items', __name__)

@bp.route('/sell-donate', methods=['GET', 'POST'])
@login_required
def sell_donate():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            category=form.category.data,
            condition=form.condition.data,
            defect_description=form.defect_description.data if form.condition.data == 'minor_defects' else None,
            specifications=form.specifications.data,
            price=0 if form.is_donation.data else form.price.data,
            is_donation=form.is_donation.data,
            is_bargainable=False if form.is_donation.data else form.is_bargainable.data,
            seller=current_user
        )
        db.session.add(item)
        db.session.commit()

        # Handle image uploads
        images = request.files.getlist('images')
        for image in images[:4]:  # Limit to 4 images
            if image and image.filename:
                image_url = save_image(image, item.id)
                item_image = ItemImage(image_url=image_url, item=item)
                db.session.add(item_image)
        
        db.session.commit()
        flash('Your item has been listed successfully!', 'success')
        return redirect(url_for('items.buy_get'))
    
    return render_template('items/sell_donate.html', title='Sell or Donate', form=form)

@bp.route('/buy-get', methods=['GET'])
def buy_get():
    page = request.args.get('page', 1, type=int)
    
    # Base query
    query = Item.query.filter_by(is_available=True)
    
    # Handle GET request with filters
    if request.args.get('filtered') == 'true':
        # Get filter values from request args
        search_query = request.args.get('query', '')
        category = request.args.get('category', 'all')
        min_price = request.args.get('min_price', 0, type=float)
        
        # Handle max_price specially since it could be empty
        max_price_str = request.args.get('max_price', '')
        max_price = float(max_price_str) if max_price_str.strip() else None
        
        condition = request.args.get('condition', 'all')
        is_donation = request.args.get('is_donation') == 'true'
        is_bargainable = request.args.get('is_bargainable') == 'true'
        sort_by = request.args.get('sort_by', 'newest')
        
        # Apply search query filter safely
        if search_query:
            # Use parameterized query pattern with wildcards
            query = query.filter(Item.name.ilike(f'%{search_query}%'))
        
        # Apply category filter
        if category and category != 'all':
            query = query.filter(Item.category == category)
        
        # Apply price filters
        if is_donation:
            query = query.filter(Item.is_donation == True)
        else:
            if min_price is not None:
                query = query.filter(Item.price >= min_price)
            if max_price is not None:
                query = query.filter(Item.price <= max_price)
        
        # Apply condition filter
        if condition and condition != 'all':
            query = query.filter(Item.condition == condition)
        
        # Apply bargainable filter
        if is_bargainable:
            query = query.filter(Item.is_bargainable == True)
        
        # Apply sorting
        if sort_by == 'newest':
            query = query.order_by(Item.date_posted.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Item.date_posted.asc())
        elif sort_by == 'price_low':
            query = query.order_by(Item.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Item.price.desc())
    else:
        # Default sorting by newest
        query = query.order_by(Item.date_posted.desc())
    
    # Debug query
    print(f"Query SQL: {query}")
    
    # Paginate results
    items = query.paginate(page=page, per_page=12, error_out=False)
    
    # Create URL for pagination with filters
    if request.args.get('filtered') == 'true':
        # Keep all current parameters for pagination, just don't include page
        args = request.args.copy()
        if 'page' in args:
            args.pop('page')
        pagination_url = url_for('items.buy_get', **args)
    else:
        pagination_url = url_for('items.buy_get')
    
    return render_template('items/buy_get.html', 
                           title='Buy or Get', 
                           items=items,
                           pagination_url=pagination_url)

@bp.route('/item/<int:id>')
def item_detail(id):
    item = Item.query.get_or_404(id)
    return render_template('items/item_detail.html', title=item.name, item=item)

@bp.route('/my-items')
@login_required
def my_items():
    items = Item.query.filter_by(seller=current_user).order_by(Item.date_posted.desc()).all()
    return render_template('items/my_items.html', title='My Items', items=items)

@bp.route('/item/<int:id>/mark-unavailable')
@login_required
def mark_unavailable(id):
    item = Item.query.get_or_404(id)
    if item.seller != current_user:
        flash('You can only mark your own items as unavailable.', 'error')
        return redirect(url_for('items.item_detail', id=id))
    
    item.is_available = False
    db.session.commit()
    flash('Item marked as unavailable.', 'success')
    return redirect(url_for('items.my_items'))

@bp.route('/wishlist')
@login_required
def wishlist():
    wishlisted_items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.date_added.desc()).all()
    return render_template('items/wishlist.html', title='My Wishlist', wishlisted_items=wishlisted_items)

@bp.route('/item/<int:id>/toggle-wishlist', methods=['POST'])
@login_required
def toggle_wishlist(id):
    item = Item.query.get_or_404(id)
    
    # Check if item is already in wishlist
    wishlist_entry = Wishlist.query.filter_by(user_id=current_user.id, item_id=id).first()
    
    if wishlist_entry:
        # Remove from wishlist
        db.session.delete(wishlist_entry)
        db.session.commit()
        flash('Item removed from wishlist!', 'success')
    else:
        # Add to wishlist
        wishlist_entry = Wishlist(user_id=current_user.id, item_id=id)
        db.session.add(wishlist_entry)
        db.session.commit()
        flash('Item added to wishlist!', 'success')
    
    # Redirect back to the referring page or item detail
    next_page = request.referrer or url_for('items.item_detail', id=id)
    return redirect(next_page) 