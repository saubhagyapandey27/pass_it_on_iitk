from flask import Blueprint, render_template
from flask_login import current_user


bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('main/index.html', title='Pass-it-on IITK')

@bp.route('/faq')
def faq():
    return render_template('main/faq.html', title='FAQ')

@bp.route('/help')
def help():
    return render_template('main/help.html', title='Help')

@bp.route('/privacy-policy')
def privacy_policy():
    return render_template('main/privacy_policy.html', title='Privacy Policy')

@bp.route('/terms-of-service')
def terms_of_service():
    return render_template('main/terms_of_service.html', title='Terms of Service') 