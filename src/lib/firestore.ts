import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
// Import the functions you need from the SDKs you need

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBlR3UdDqxDHZCIW19ELuN6wIOuj5TfOzU",
    authDomain: "smartfile-422907.firebaseapp.com",
    projectId: "smartfile-422907",
    storageBucket: "smartfile-422907.appspot.com",
    messagingSenderId: "414550313170",
    appId: "1:414550313170:web:616e97419c570dab76850b"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

export const db = getFirestore(app);