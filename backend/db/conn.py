import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "races.db")

def get_conn():
    return sqlite3.connect(DB_PATH)
