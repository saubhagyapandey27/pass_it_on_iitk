from flask import Blueprint, render_template, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import BuyRequest, Item
from app.utils import send_interest_notification, send_request_accepted_notification

bp = Blueprint('requests', __name__)

@bp.route('/buying-requests')
@login_required
def buying_requests():
    sent_requests = BuyRequest.query.filter_by(buyer=current_user).order_by(BuyRequest.date_requested.desc()).all()
    received_requests = BuyRequest.query.filter_by(seller=current_user).order_by(BuyRequest.date_requested.desc()).all()
    return render_template('requests/buying_requests.html', 
                         title='Buying Requests',
                         sent_requests=sent_requests,
                         received_requests=received_requests)

@bp.route('/show-interest/<int:item_id>')
@login_required
def show_interest(item_id):
    item = Item.query.get_or_404(item_id)
    
    if item.seller == current_user:
        flash('You cannot show interest in your own item.', 'error')
        return redirect(url_for('items.item_detail', id=item_id))
    
    # Check if request already exists
    existing_request = BuyRequest.query.filter_by(
        buyer=current_user,
        item=item,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You have already shown interest in this item.', 'info')
        return redirect(url_for('items.item_detail', id=item_id))
    
    buy_request = BuyRequest(
        buyer=current_user,
        seller=item.seller,
        item=item
    )
    db.session.add(buy_request)
    db.session.commit()
    
    # Send email notification to seller
    send_interest_notification(item.seller.email, current_user.name, item.name)
    
    flash('Your interest has been sent to the seller.', 'success')
    return redirect(url_for('requests.buying_requests'))

@bp.route('/accept-request/<int:request_id>')
@login_required
def accept_request(request_id):
    buy_request = BuyRequest.query.get_or_404(request_id)
    
    if buy_request.seller != current_user:
        flash('You can only accept requests for your own items.', 'error')
        return redirect(url_for('requests.buying_requests'))
    
    buy_request.status = 'accepted'
    db.session.commit()
    
    # Send email notification to buyer
    send_request_accepted_notification(buy_request.buyer.email, current_user.name, buy_request.item.name)
    
    flash('Request accepted successfully.', 'success')
    return redirect(url_for('requests.buying_requests'))

@bp.route('/decline-request/<int:request_id>')
@login_required
def decline_request(request_id):
    buy_request = BuyRequest.query.get_or_404(request_id)
    
    if buy_request.seller != current_user:
        flash('You can only decline requests for your own items.', 'error')
        return redirect(url_for('requests.buying_requests'))
    
    buy_request.status = 'declined'
    db.session.commit()
    
    flash('Request declined.', 'success')
    return redirect(url_for('requests.buying_requests'))

@bp.route('/get-seller-contact/<int:request_id>')
@login_required
def get_seller_contact(request_id):
    buy_request = BuyRequest.query.get_or_404(request_id)
    
    if buy_request.buyer != current_user:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if buy_request.status != 'accepted':
        return jsonify({'error': 'Request not accepted yet'}), 400
    
    return jsonify({
        'seller_name': buy_request.seller.name,
        'seller_mobile': buy_request.seller.mobile
    }) 