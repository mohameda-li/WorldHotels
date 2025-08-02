from flask import Flask, render_template
from routes import register_blueprints
from db import get_connection
from config import Config

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config)
app.secret_key = 'secret.key'

# ---------- Static Page Routes ----------
@app.route('/')
def main_page():
    return render_template('projectMainPage.html')

@app.route('/Information.html')
def info():
    return render_template('Information.html')

@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/signUp.html')
def signup():
    return render_template('signUp.html')

@app.route('/booking.html', methods=['GET'])
def show_booking_form():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT HotelID, HotelName FROM Hotel")
        hotels = cursor.fetchall()
    return render_template('booking.html', hotels=hotels)

@app.route('/ForgotPassword.html')
def forgot_password():
    return render_template('ForgotPassword.html')

@app.route('/change_password.html')
def change_password():
    return render_template('change_password.html')

# ---------- Register Blueprints ----------
register_blueprints(app)

# ---------- Run Application ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
