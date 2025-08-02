from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_connection
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Admin-only access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Admin access required.")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# Admin Dashboard
@admin_bp.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT HotelID, HotelName, Capacity FROM Hotel")
        hotels = cursor.fetchall()
    return render_template('AdminDashboard.html', hotels=hotels)


# -------------------- HOTEL ROUTES --------------------

@admin_bp.route('/manage_hotels')
@admin_required
def manage_hotels():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT HotelID, HotelName, Capacity FROM Hotel")
        hotels = cursor.fetchall()
    return render_template('modify_Hotels.html', hotels=hotels)


@admin_bp.route('/add_hotel', methods=['POST'])
@admin_required
def add_hotel():
    name = request.form['hotelName']
    capacity = request.form['capacity']
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Hotel (HotelName, Capacity) VALUES (%s, %s)", (name, capacity))
        conn.commit()
    flash("Hotel added successfully.")
    return redirect(url_for('admin.manage_hotels'))


from mysql.connector.errors import IntegrityError

@admin_bp.route('/delete_hotel/<int:hotel_id>')
@admin_required
def delete_hotel(hotel_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Hotel WHERE HotelID = %s", (hotel_id,))
            conn.commit()
            flash("Hotel deleted successfully.", "success")
        except IntegrityError:
            flash("Cannot delete hotel: it is linked to rooms or bookings.", "error")
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "error")
    return redirect(url_for('admin.manage_hotels'))




# -------------------- USER ROUTES --------------------

@admin_bp.route('/manage_users')
@admin_required
def manage_users():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Username, Email, Role FROM User")
        users = cursor.fetchall()
    return render_template('manage_users.html', users=users)


from mysql.connector.errors import IntegrityError

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM User WHERE UserID = %s", (user_id,))
            conn.commit()
            flash("User deleted successfully.", "success")
        except IntegrityError as e:
            flash("Cannot delete user: they are linked to existing bookings or other data.", "error")
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "error")
    return redirect(url_for('admin.manage_users'))



@admin_bp.route('/change_role/<int:user_id>', methods=['POST'])
@admin_required
def change_role(user_id):
    new_role = request.form['role']
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE User SET Role = %s WHERE UserID = %s", (new_role, user_id))
        conn.commit()
    flash("User role updated successfully.")
    return redirect(url_for('admin.manage_users'))


# -------------------- BOOKING ROUTES --------------------

@admin_bp.route('/manage_bookings')
@admin_required
def manage_bookings():
    query = request.args.get('query', '').strip()
    with get_connection() as conn:
        cursor = conn.cursor()

        if query:
            if query.isdigit():
                cursor.execute("""
                    SELECT b.BookingID, b.UserID, b.HotelID, b.RoomID, b.CheckIn, b.CheckOut, b.NoOfGuests, b.Status
                    FROM Booking b
                    WHERE b.BookingID = %s
                """, (int(query),))
            else:
                cursor.execute("""
                    SELECT b.BookingID, b.UserID, b.HotelID, b.RoomID, b.CheckIn, b.CheckOut, b.NoOfGuests, b.Status
                    FROM Booking b
                    JOIN User u ON b.UserID = u.UserID
                    WHERE u.Username LIKE %s
                """, (f"%{query}%",))
        else:
            cursor.execute("""
                SELECT BookingID, UserID, HotelID, RoomID, CheckIn, CheckOut, NoOfGuests, Status
                FROM Booking
            """)
        bookings = cursor.fetchall()
    return render_template("modify_Bookings.html", bookings=bookings)


@admin_bp.route('/delete_booking/<int:booking_id>')
@admin_required
def delete_booking(booking_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Booking WHERE BookingID = %s", (booking_id,))
            conn.commit()
            flash("Booking deleted.")
        except Exception:
            flash("Cannot delete booking: related cancellation exists.")
    return redirect(url_for('admin.manage_bookings'))


@admin_bp.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@admin_required
def edit_booking(booking_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            room_id = request.form['roomID']
            check_in = request.form['checkIn']
            check_out = request.form['checkOut']
            guests = request.form['noOfGuests']
            status = request.form['status']

            cursor.execute("""
                UPDATE Booking
                SET RoomID = %s, CheckIn = %s, CheckOut = %s, NoOfGuests = %s, Status = %s
                WHERE BookingID = %s
            """, (room_id, check_in, check_out, guests, status, booking_id))
            conn.commit()
            flash("Booking updated.")
            return redirect(url_for('admin.manage_bookings'))

        cursor.execute("""
            SELECT RoomID, CheckIn, CheckOut, NoOfGuests, Status
            FROM Booking
            WHERE BookingID = %s
        """, (booking_id,))
        booking = cursor.fetchone()

    return render_template("edit_booking.html", booking_id=booking_id, booking=booking)
