
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('fileprocessing/smartfile-422907-2f9ca6d83372.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()