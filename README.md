# Pass-it-on IITK

A platform for IITK students to buy, sell, and donate used items within the campus community.

## Features

- User authentication with email verification
- Item listing with multiple images
- Search and filter functionality
- Wishlist system
- Request system for buyers to express interest
- Admin panel for moderation

## Deployment Guide

### Prerequisites

1. A [Render](https://render.com/) account
2. A [Cloudinary](https://cloudinary.com/) account
3. An email account for sending notifications

### Cloudinary Setup

1. Sign up for a free Cloudinary account
2. Note your Cloud name, API Key, and API Secret from the Dashboard

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the following settings:
   - **Name**: pass-it-on-iitk (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

4. Add the following environment variables:
   - `FLASK_ENV`: production
   - `SECRET_KEY`: (generate a secure random key)
   - `MAIL_SERVER`: (your SMTP server)
   - `MAIL_PORT`: (your SMTP port, typically 587)
   - `MAIL_USE_TLS`: True
   - `MAIL_USERNAME`: (your email username)
   - `MAIL_PASSWORD`: (your email password or app password)
   - `ADMIN_EMAIL`: (your admin email)
   - `CLOUDINARY_CLOUD_NAME`: (your Cloudinary cloud name)
   - `CLOUDINARY_API_KEY`: (your Cloudinary API key)
   - `CLOUDINARY_API_SECRET`: (your Cloudinary API secret)

5. Create a PostgreSQL database on Render
   - Go to the Render Dashboard > New > PostgreSQL
   - Note the Internal Database URL
   - Add it as an environment variable in your Web Service:
     - `DATABASE_URL`: (your PostgreSQL connection string)

6. Deploy your application

### Database Migration

After deployment, you'll need to run migrations to set up the database schema:

1. Connect to your Render service shell
2. Run the following commands:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## Local Development

1. Clone the repository
2. Create a virtual environment: `conda create -n yt python=3.10`
3. Activate the environment: `conda activate yt`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with the required environment variables
6. Run the application: `python run.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Project Structure

```
pass_it_on_iitk/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   ├── utils.py
│   ├── static/
│   └── templates/
├── instance/
├── migrations/
├── venv/
├── .env
├── .gitignore
├── config.py
├── requirements.txt
└── README.md
``` 