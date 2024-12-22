import os
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv  # Import load_dotenv to load .env variables

# Load environment variables from .env file
load_dotenv()
# Retrieve Firebase credentials from Replit secrets
firebase_creds = os.getenv('FIREBASE_CREDENTIALS')

# Save the Firebase credentials to a temporary file
with open('firebase_creds.json', 'w') as f:
    f.write(firebase_creds)

# Initialize Firebase Admin with the credentials from the temporary file
try:
    cred = credentials.Certificate('firebase_creds.json')
    initialize_app(cred)  # Only call once
except ValueError:
    pass  # Ignore if already initialized

db = firestore.client()  # Shared Firestore client

os.remove('firebase_creds.json')
