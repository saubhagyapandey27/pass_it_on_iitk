from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Item, BuyRequest, ItemImage, Wishlist

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.email != current_app.config['ADMIN_EMAIL']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    users_count = User.query.count()
    items_count = Item.query.count()
    requests_count = BuyRequest.query.count()
    return render_template('admin/dashboard.html', users_count=users_count, 
                           items_count=items_count, requests_count=requests_count)

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/items')
@login_required
@admin_required
def items():
    items = Item.query.all()
    return render_template('admin/items.html', items=items)

@bp.route('/requests')
@login_required
@admin_required
def requests():
    requests = BuyRequest.query.all()
    return render_template('admin/requests.html', requests=requests)

@bp.route('/delete-user/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot delete your own account from admin panel.', 'danger')
    else:
        # Delete related records
        BuyRequest.query.filter_by(buyer=user).delete()
        BuyRequest.query.filter_by(seller=user).delete()
        Wishlist.query.filter_by(user_id=user.id).delete()
        
        # Delete user's items and their images
        for item in Item.query.filter_by(seller=user).all():
            ItemImage.query.filter_by(item_id=item.id).delete()
            item.requests.delete()
        Item.query.filter_by(seller=user).delete()
        
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} has been deleted.', 'success')
    
    return redirect(url_for('admin.users'))

@bp.route('/delete-item/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    # Delete related records
    ItemImage.query.filter_by(item_id=item.id).delete()
    BuyRequest.query.filter_by(item=item).delete()
    Wishlist.query.filter_by(item=item).delete()
    
    db.session.delete(item)
    db.session.commit()
    flash(f'Item {item.name} has been deleted.', 'success')
    
    return redirect(url_for('admin.items'))

@bp.route('/delete-request/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_request(id):
    request = BuyRequest.query.get_or_404(id)
    db.session.delete(request)
    db.session.commit()
    flash(f'Request has been deleted.', 'success')
    return redirect(url_for('admin.requests'))

@bp.route('/fix-image-urls')
@login_required
@admin_required
def fix_image_urls():
    """Maintenance route to fix any broken image URLs in the database"""
    import os
    import cloudinary
    from flask import current_app
    
    # Count of different types of fixes
    fixes = {
        'missing': 0,
        'local_to_default': 0,
        'deleted': 0
    }
    
    # Check if Cloudinary is configured
    cloudinary_configured = (
        os.environ.get('CLOUDINARY_URL') or 
        (os.environ.get('CLOUDINARY_CLOUD_NAME') and 
         os.environ.get('CLOUDINARY_API_KEY') and 
         os.environ.get('CLOUDINARY_API_SECRET'))
    )
    
    # Get all image entries
    images = ItemImage.query.all()
    current_app.logger.info(f"Checking {len(images)} image entries")
    
    for image in images:
        # Case 1: Empty URL - delete the image entry
        if not image.image_url:
            current_app.logger.info(f"Deleting image entry with no URL for item {image.item_id}")
            db.session.delete(image)
            fixes['deleted'] += 1
            continue
            
        # Case 2: Local storage URL in production (unusable) - use a default
        if not image.image_url.startswith('http') and os.environ.get('FLASK_ENV') == 'production':
            current_app.logger.info(f"Local storage URL in production for item {image.item_id}: {image.image_url}")
            # Remove this image record as it's not usable in production
            db.session.delete(image)
            fixes['local_to_default'] += 1
    
    # Commit all changes
    db.session.commit()
    
    return render_template('admin/maintenance.html', 
                          title='Image URL Fixes', 
                          fixes=fixes, 
                          total_fixed=sum(fixes.values()))
