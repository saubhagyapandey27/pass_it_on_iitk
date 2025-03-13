"""
Security configuration for Pass-it-on IITK
This file contains settings that help secure the application
"""

# CSRF Protection
CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

# Password Policy
MIN_PASSWORD_LENGTH = 8
REQUIRE_SPECIAL_CHARS = True

# Login Attempts
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_TIMEOUT = 300  # 5 minutes

# Session Security
SESSION_TIMEOUT = 3600  # 1 hour

# File Upload Restrictions
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 