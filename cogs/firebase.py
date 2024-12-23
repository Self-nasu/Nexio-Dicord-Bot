import os
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv 

load_dotenv()
firebase_creds = os.getenv('FIREBASE_CREDENTIALS')

with open('firebase_creds.json', 'w') as f:
    f.write(firebase_creds)

try:
    cred = credentials.Certificate('firebase_creds.json')
    initialize_app(cred)
except ValueError:
    pass  

db = firestore.client()  

os.remove('firebase_creds.json')
