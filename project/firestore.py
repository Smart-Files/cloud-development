import firebase_admin
from firebase_admin import credentials, firestore
from project.logger import logger
import os


cred = None
firestore_app = None
db = None


if os.path.exists('/firebase/firebase_service_account.json'):
    logger.info('Firebase service account found, initializing Firestore...')
    cred = credentials.Certificate('/firebase/firebase_service_account.json')
    firestore_app = firebase_admin.initialize_app(cred)
    db = firestore.client(firestore_app)
else:
    logger.warning('Firebase service account not found, Firestore not initialized.')
    logger.info('Directory contents: %s', os.listdir('/firebase'))

