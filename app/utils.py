import os
import secrets
import imghdr
from PIL import Image
from flask import current_app, abort
from flask_mail import Message
from app import mail
from threading import Thread
import cloudinary
import cloudinary.uploader
from io import BytesIO

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body=None):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_otp_email(user_email, otp):
    subject = 'Pass-it-on IITK - Email Verification'
    sender = current_app.config['MAIL_USERNAME']
    text_body = f'''Your OTP for Pass-it-on IITK email verification is: {otp}
    
Please enter this OTP on the verification page to complete your registration.
This OTP will expire in 10 minutes.

Best regards,
Pass-it-on IITK Team'''
    
    send_email(subject, sender, [user_email], text_body)

def send_interest_notification(seller_email, buyer_name, item_name):
    subject = f'New Interest in Your Item - {item_name}'
    sender = current_app.config['MAIL_USERNAME']
    text_body = f'''Hello,

{buyer_name} is interested in buying your item "{item_name}".
Please visit the "Buying Requests" page on Pass-it-on IITK to accept or decline the request.

Best regards,
Pass-it-on IITK Team'''
    
    send_email(subject, sender, [seller_email], text_body)

def send_request_accepted_notification(buyer_email, seller_name, item_name):
    subject = f'Request Accepted - {item_name}'
    sender = current_app.config['MAIL_USERNAME']
    text_body = f'''Hello,

{seller_name} has accepted your request to buy "{item_name}".
Please visit the "Buying Requests" page on Pass-it-on IITK to view the seller's contact details.

Best regards,
Pass-it-on IITK Team'''
    
    send_email(subject, sender, [buyer_email], text_body)

def validate_image(file_stream):
    """Additional validation for image content."""
    try:
        image = Image.open(file_stream)
        image.verify()  # Verify image integrity
        file_stream.seek(0)  # Reset file pointer
        return True
    except:
        return False

def save_image(image_file, item_id):
    # Verify file extension
    file_ext = os.path.splitext(image_file.filename)[1].lower()
    if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        abort(400, "Unsupported file format")
    
    # Additional check of file content
    file_content = image_file.read()
    image_file.seek(0)  # Reset file pointer
    
    image_type = imghdr.what(None, file_content)
    if image_type not in ['jpeg', 'png', 'gif']:
        abort(400, "Invalid image content")
    
    # Additional validation for image integrity
    if not validate_image(image_file):
        abort(400, "Invalid image content")
        
    # Random hex for unique filename
    random_hex = secrets.token_hex(8)
    
    # Open and process image
    image = Image.open(image_file)
    
    # Resize image to reduce size
    output_size = (800, 800)  # Max dimensions while maintaining aspect ratio
    image.thumbnail(output_size)
    
    # Save to BytesIO object for Cloudinary upload
    img_io = BytesIO()
    
    # Optimize based on format
    if file_ext in ['.jpg', '.jpeg']:
        image.save(img_io, 'JPEG', quality=85)
    elif file_ext == '.png':
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        image.save(img_io, 'JPEG', quality=85)
    else:
        image.save(img_io, format=image_type.upper())
    
    img_io.seek(0)
    
    # Check if any of the Cloudinary environment variables are set
    cloudinary_configured = (
        os.environ.get('CLOUDINARY_URL') or 
        (os.environ.get('CLOUDINARY_CLOUD_NAME') and 
         os.environ.get('CLOUDINARY_API_KEY') and 
         os.environ.get('CLOUDINARY_API_SECRET'))
    )
    
    # Always try to use Cloudinary first when deployed
    if cloudinary_configured:
        try:
            current_app.logger.info(f"Attempting to upload image to Cloudinary for item {item_id}")
            
            # Make sure we're using the correct module for uploader
            upload_params = {
                'folder': "pass-it-on-iitk",
                'public_id': f"item_{item_id}_{random_hex}"
            }
            
            response = cloudinary.uploader.upload(img_io, **upload_params)
            
            if 'secure_url' in response:
                cloudinary_url = response['secure_url']
                current_app.logger.info(f"Successfully uploaded to Cloudinary: {cloudinary_url}")
                return cloudinary_url
            else:
                current_app.logger.error(f"Cloudinary response missing secure_url: {response}")
                raise Exception("Invalid Cloudinary response")
                
        except Exception as e:
            current_app.logger.error(f"Cloudinary upload failed: {str(e)}")
            # Fall back to local storage only if not in production
            if os.environ.get('FLASK_ENV') == 'production':
                current_app.logger.error("Cannot fall back to local storage in production! Using default image.")
                return None
    
    # Local storage as fallback (for development) or if Cloudinary not configured
    current_app.logger.info(f"Using local storage for image (item {item_id})")
    image_filename = f'item_{item_id}_{random_hex}{file_ext}'
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
    
    # Save locally
    if file_ext in ['.jpg', '.jpeg']:
        image.save(image_path, 'JPEG', quality=85)
    elif file_ext == '.png':
        image.save(image_path, 'PNG', optimize=True)
    else:
        image.save(image_path, optimize=True)
    
    return image_filename

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)  # 6-digit OTP 

def send_password_reset_email(user_email, otp):
    subject = 'Pass-it-on IITK - Password Reset'
    sender = current_app.config['MAIL_USERNAME']
    text_body = f'''Your OTP for Pass-it-on IITK password reset is: {otp}
    
Please enter this OTP on the password reset page to reset your password.
This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

Best regards,
Pass-it-on IITK Team'''
    
    send_email(subject, sender, [user_email], text_body)
