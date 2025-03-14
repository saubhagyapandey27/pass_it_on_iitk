from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Regexp, EqualTo
import re
from security_config import MIN_PASSWORD_LENGTH

def validate_mobile(form, field):
    if not re.match(r'^\d{10}$', field.data):
        raise ValidationError('Enter a valid 10-digit mobile number')

def validate_password_strength(form, field):
    password = field.data
    
    # Check length
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Password must be at least {MIN_PASSWORD_LENGTH} characters long')
    
    # Check for at least one uppercase letter
    if not any(c.isupper() for c in password):
        raise ValidationError('Password must contain at least one uppercase letter')
    
    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        raise ValidationError('Password must contain at least one number')
    
    # Check for at least one special character
    if not any(c in '!@#$%^&*()_-+={}[]|:;<>,.?/~`' for c in password):
        raise ValidationError('Password must contain at least one special character')

class LoginForm(FlaskForm):
    email = StringField('IITK Email', validators=[
        DataRequired(),
        Email(),
        Regexp(r'.*@iitk\.ac\.in$', message='Must be an IITK email address')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class SignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('IITK Email', validators=[
        DataRequired(),
        Email(),
        Regexp(r'.*@iitk\.ac\.in$', message='Must be an IITK email address')
    ])
    batch_choices = [
        ('UG1', 'Undergrad 1st Year'),
        ('UG2', 'Undergrad 2nd Year'),
        ('UG3', 'Undergrad 3rd Year'),
        ('UG4', 'Undergrad 4th Year'),
        ('PG1', 'Postgrad 1st Year'),
        ('PG2', 'Postgrad 2nd Year'),
        ('PhD1', 'PhD 1st Year'),
        ('PhD2', 'PhD 2nd Year'),
        ('PhD3', 'PhD 3rd Year'),
        ('PhD4', 'PhD 4th Year'),
        ('PhD5', 'PhD 5th Year')
    ]
    batch = SelectField('Batch', choices=batch_choices, validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired(), Length(max=64)])
    mobile = StringField('Mobile Number (only shown after request approval)', 
                        validators=[
                            DataRequired(), 
                            validate_mobile
                        ])
    iitk_address = StringField('IITK Address (e.g., H2 G-175) (only shown after request approval)', validators=[
        DataRequired(),
        Length(max=20)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        validate_password_strength
    ])
    submit = SubmitField('Next')

class OTPVerificationForm(FlaskForm):
    otp = StringField('Enter OTP', validators=[
        DataRequired(),
        Length(min=6, max=6),
        Regexp(r'^\d{6}$', message='OTP must be 6 digits')
    ])
    submit = SubmitField('Verify OTP')

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    category_choices = [
        ('electronics', 'Electronics'),
        ('books', 'Books'),
        ('furniture', 'Furniture'),
        ('bicycles', 'Bicycles'),
        ('clothing', 'Clothing'),
        ('sports', 'Sports Equipment'),
        ('kitchen', 'Kitchen Appliances'),
        ('stationery', 'Stationery'),
        ('other', 'Other')
    ]
    category = SelectField('Category', choices=category_choices, validators=[DataRequired()])
    condition_choices = [
        ('good', 'Good'),
        ('minor_defects', 'Minor Defects')
    ]
    condition = SelectField('Condition', choices=condition_choices, validators=[DataRequired()])
    defect_description = TextAreaField('Defect Description')
    specifications = TextAreaField('Specifications', validators=[DataRequired()])
    price = FloatField('Price (₹)')
    is_donation = BooleanField('Donate for Free')
    is_bargainable = BooleanField('Bargainable')
    images = FileField('Upload Images (Max 2)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ], render_kw={"multiple": True})
    submit = SubmitField('List Item')

    def validate_defect_description(self, field):
        if self.condition.data == 'minor_defects' and not field.data:
            raise ValidationError('Please describe the defects when condition is "Minor Defects"')
    
    def validate_price(self, field):
        if not self.is_donation.data and (field.data is None or field.data < 0):
            raise ValidationError('Please enter a valid price (0 or greater) when not donating')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('IITK Email', validators=[
        DataRequired(),
        Email(),
        Regexp(r'.*@iitk\.ac\.in$', message='Must be an IITK email address')
    ])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    otp = StringField('Enter OTP', validators=[
        DataRequired(),
        Length(min=6, max=6),
        Regexp(r'^\d{6}$', message='OTP must be 6 digits')
    ])
    password = PasswordField('New Password', validators=[
        DataRequired(), 
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Length(max=100)])
    category = SelectField('Category', choices=[('all', 'All Categories')], validators=[])
    min_price = FloatField('Min Price', validators=[], default=0)
    max_price = FloatField('Max Price', validators=[])
    condition = SelectField('Condition', choices=[
        ('all', 'All Conditions'),
        ('good', 'Good'),
        ('minor_defects', 'Minor Defects')
    ], validators=[])
    is_donation = BooleanField('Free Items Only')
    is_bargainable = BooleanField('Bargainable Only')
    sort_by = SelectField('Sort By', choices=[
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low')
    ], validators=[])
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        # Dynamically add categories from ItemForm
        self.category.choices = [('all', 'All Categories')] + ItemForm.category_choices 