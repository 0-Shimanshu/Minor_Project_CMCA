import os
from dotenv import load_dotenv

# Resolve project root and app directory
APP_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, '..'))
ENV_PATH = os.path.join(ROOT_DIR, '.env')

# Load environment variables from project root
load_dotenv(ENV_PATH)

# Absolute path to SQLite database file within app/database/app.db
DB_PATH = os.path.abspath(os.path.join(APP_DIR, 'database', 'app.db'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Institution domain for branding, URLs, and email fallbacks
    COLLEGE_DOMAIN = os.getenv('COLLEGE_DOMAIN')
