"""
Vercel Flask Detection Bypass
This file exists to satisfy Vercel's Flask auto-detection requirement.
The actual website is a static site in public/ directory.
API endpoints are Serverless Functions in api/ directory.
"""

# Minimal Flask app to prevent build errors
from flask import Flask, redirect

app = Flask(__name__)

@app.route('/')
def index():
    # Redirect to public/index.html (handled by Vercel rewrites)
    return redirect('/index.html')

if __name__ == '__main__':
    # This won't be executed on Vercel
    app.run()
