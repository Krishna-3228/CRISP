import flask 
from flask import Flask, render_template, redirect, request, url_for
import requests
import sqlite3


app = Flask(__name__)

PORT = 8001

@app.route('/', methods=['GET'])
def home():
    database = sqlite3.connect('./Captured_requests.db')
    cursor = database.cursor()
    entries = cursor.execute('select * from all_requests order by Request_Number desc')
    
    return render_template("home.html", entries=entries)

def delete_all_records():
    database = sqlite3.connect('./Captured_requests.db')
    cursor = database.cursor()
    cursor.execute('delete from all_requests')
    database.commit()
    database.close()

@app.route('/dropallrequests', methods=['POST'])
def dropallrequests():
    delete_all_records()
    return redirect(url_for("home"))  # Redirect back to home page

if __name__ == "__main__":
    app.run(port=PORT)