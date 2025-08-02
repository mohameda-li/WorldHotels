from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection

auth_bp = Blueprint('auth', __name__)


# -------------------- LOGIN --------------------
@auth_bp.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['password']

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT UserID, HashedPassword, Role FROM User WHERE Username = %s", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['role'] = user[2]
            session['username'] = username
            flash(f"Welcome back, {username}!")
            return redirect(url_for('main_page'))

        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


# -------------------- SIGN UP --------------------
@auth_bp.route('/signUp', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        firstname = request.form['FirstName']
        lastname = request.form['LastName']
        email = request.form['Email']
        username = request.form['Username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO User (Username, FirstName, LastName, Email, HashedPassword, Role)
                VALUES (%s, %s, %s, %s, %s, 'customer')
            """, (username, firstname, lastname, email, hashed_password))
            conn.commit()

            cursor.execute("SELECT UserID FROM User WHERE Username = %s", (username,))
            user_id = cursor.fetchone()[0]

        session['user_id'] = user_id
        session['username'] = username
        session['role'] = 'customer'

        return render_template('WelcomePage.html')

    return render_template('signUp.html')


# -------------------- LOGOUT --------------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main_page'))


# -------------------- FORGOT PASSWORD --------------------
@auth_bp.route('/ForgotPassword.html')
def forgot_password():
    return render_template('ForgotPassword.html')


@auth_bp.route('/check_username', methods=['POST'])
def check_username():
    username = request.form['Username']

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE Username = %s", (username,))
        user = cursor.fetchone()

    if user:
        session['username_for_password_change'] = username
        return render_template('ChangePassword.html')

    flash("Username not found. Please try again.")
    return redirect(url_for('auth.forgot_password'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        password = request.form['password']
        username = session.get('username_for_password_change')

        if not username:
            return "Username not found, please retry the process.", 400

        hashed_password = generate_password_hash(password)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE User SET HashedPassword = %s WHERE Username = %s", (hashed_password, username))
            conn.commit()

        flash('Password updated successfully.')
        return redirect(url_for('auth.login'))

    return render_template('ChangePassword.html')
