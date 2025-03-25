import firebase_admin
from firebase_admin import credentials, firestore_async as firestore
from project.logger import logger
import os


cred = None
firestore_app = None
db = None


if os.path.exists('/firebase/serviceAccountKey.json'):
    logger.info('Firebase production service account found, initializing Firestore...')
    cred = credentials.Certificate('/firebase/serviceAccountKey.json')
    firestore_app = firebase_admin.initialize_app(cred)
    db = firestore.client(firestore_app)
elif os.path.exists("serviceAccountKey.json"):
    logger.warning('Firebase local service account found, Firestore initializing...')
    cred = credentials.Certificate('serviceAccountKey.json')
    firestore_app = firebase_admin.initialize_app(cred)
    db = firestore.client(firestore_app)

