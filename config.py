import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for session management and flash messages
    SECRET_KEY = os.environ.get('SECRET_KEY', 'college-mini-project-secret-key-12345')

    # SQLite Database file location
    DATABASE = os.path.join(BASE_DIR, 'tracker.db')

    # Path to the curated hackathons JSON file
    HACKATHONS_FILE = os.path.join(BASE_DIR, 'data', 'hackathons.json')

    # Cache duration for API responses (in seconds): 1 hour = 3600 seconds
    CACHE_DURATION = 3600
