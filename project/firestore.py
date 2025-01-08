import firebase_admin
from firebase_admin import credentials, firestore_async as firestore
from project.logger import logger
import os


cred = None
firestore_app = None
db = None


if os.path.exists('/firebase/firebase_service_account.json'):
    logger.info('Firebase production service account found, initializing Firestore...')
    cred = credentials.Certificate('/firebase/firebase_service_account.json')
    firestore_app = firebase_admin.initialize_app(cred)
    db = firestore.client(firestore_app)
elif os.path.exists("firebase_service_account.json"):
    logger.warning('Firebase local service account found, Firestore initializing...')
    cred = credentials.Certificate('firebase_service_account.json')
    firestore_app = firebase_admin.initialize_app(cred)
    db = firestore.client(firestore_app)

