"""
Dummy Flask app to satisfy Vercel's framework detection.
This project is actually a static website + API functions.
"""
from flask import Flask

app = Flask(__name__)

# Empty app - actual routes handled by Vercel rewrites
