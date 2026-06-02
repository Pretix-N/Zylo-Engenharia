import { initializeApp } from 'firebase/app'
import { getDatabase } from 'firebase/database'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: "AIzaSyC9Tf6JRIj4n2nPTZ2Xhe7nFf5h9CkvZzo",
  authDomain: "zyloengenharia.firebaseapp.com",
  databaseURL: "https://zyloengenharia-default-rtdb.firebaseio.com",
  projectId: "zyloengenharia",
  storageBucket: "zyloengenharia.firebasestorage.app",
  messagingSenderId: "294016996424",
  appId: "1:294016996424:web:cb04086882318c4b04347d"
}

const app = initializeApp(firebaseConfig)
export const db = getDatabase(app)
export const auth = getAuth(app)
