
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os


cred = None
firestore_app = None
db = None


if os.path.exists('/firebase/firebase_service_account.json'):
    cred = credentials.Certificate('/firebase/firebase_service_account.json')
    firestore_app = firebase_admin.initialize_app(cred)
    db = firestore.client()