
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os


cred = None
app = None
db = None


if os.path.exists('smartfile-account.json'):
    cred = credentials.Certificate('smartfile-account.json')
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()