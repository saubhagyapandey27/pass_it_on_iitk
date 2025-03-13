from flask import Blueprint, render_template, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, SignupForm, OTPVerificationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.utils import generate_otp, send_otp_email, send_password_reset_email
from datetime import datetime, timedelta
# app/routes/auth.py - Apply rate limiting to authentication endpoints
from app import limiter

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        if not user.is_verified:
            # Store email in session for resend OTP
            session['signup_email'] = user.email
            flash('Please verify your email first. Click here to resend OTP.', 'error')
            return redirect(url_for('auth.resend_otp'))
        
        # Clear and regenerate session to prevent session fixation
        session.clear()
        login_user(user)
        return redirect(url_for('main.index'))
    
    return render_template('auth/login.html', title='Login', form=form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. If you haven\'t verified your email, click here to resend OTP.', 'error')
            session['signup_email'] = form.email.data
            return redirect(url_for('auth.resend_otp'))
        
        # Store user data in session
        session['user_data'] = {
            'name': form.name.data,
            'email': form.email.data,
            'batch': form.batch.data,
            'department': form.department.data,
            'mobile': form.mobile.data,
            'iitk_address': form.iitk_address.data,
            'password': form.password.data
        }
        
        # Generate and send OTP
        otp = generate_otp()
        session['signup_email'] = form.email.data
        session['otp'] = otp
        session['otp_expiry'] = (datetime.utcnow() + timedelta(minutes=10)).timestamp()
        
        send_otp_email(form.email.data, otp)
        
        return redirect(url_for('auth.verify_otp'))
    
    return render_template('auth/signup.html', title='Sign Up', form=form)

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if 'signup_email' not in session or 'user_data' not in session:
        return redirect(url_for('auth.signup'))
    
    form = OTPVerificationForm()
    if form.validate_on_submit():
        if datetime.utcnow().timestamp() > session['otp_expiry']:
            flash('OTP has expired. Please try again.', 'error')
            return redirect(url_for('auth.resend_otp'))
        
        if form.otp.data == session['otp']:
            # Create user only after OTP verification
            user_data = session['user_data']
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                batch=user_data['batch'],
                department=user_data['department'],
                mobile=user_data['mobile'],
                iitk_address=user_data['iitk_address'],
                is_verified=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            db.session.commit()
            
            # Clear session data
            session.pop('signup_email', None)
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('user_data', None)
            
            flash('Email verified successfully! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP', 'error')
    
    return render_template('auth/verify_otp.html', title='Verify OTP', form=form)

@bp.route('/resend-otp')
@limiter.limit("3 per minute")
def resend_otp():
    if 'signup_email' not in session:
        return redirect(url_for('auth.signup'))
    
    # Generate and send new OTP
    otp = generate_otp()
    session['otp'] = otp
    session['otp_expiry'] = (datetime.utcnow() + timedelta(minutes=10)).timestamp()
    
    send_otp_email(session['signup_email'], otp)
    flash('New OTP has been sent to your email.', 'info')
    
    return redirect(url_for('auth.verify_otp'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    # Clear session data
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/reset-password-request', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate and send OTP
            otp = generate_otp()
            session['reset_email'] = user.email
            session['reset_otp'] = otp
            session['reset_otp_expiry'] = (datetime.utcnow() + timedelta(minutes=10)).timestamp()
            
            send_password_reset_email(user.email, otp)
            
            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('No account found with that email address.', 'error')
    
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if 'reset_email' not in session:
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if datetime.utcnow().timestamp() > session['reset_otp_expiry']:
            flash('OTP has expired. Please try again.', 'error')
            return redirect(url_for('auth.reset_password_request'))
        
        if form.otp.data == session['reset_otp']:
            user = User.query.filter_by(email=session['reset_email']).first()
            if user:
                user.set_password(form.password.data)
                db.session.commit()
                
                # Clear session data
                session.pop('reset_email', None)
                session.pop('reset_otp', None)
                session.pop('reset_otp_expiry', None)
                
                flash('Your password has been reset successfully! Please login.', 'success')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP', 'error')
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)
