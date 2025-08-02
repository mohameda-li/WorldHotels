from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from decimal import Decimal
from db import get_connection

booking_bp = Blueprint('booking', __name__)

# ---------------- PRICE CALCULATION ---------------- #

def calculate_total_price(check_in_date_str, check_out_date_str, booking_date_str, hotel_id, room_type_id, num_guests, db_cursor):
    check_in = datetime.strptime(check_in_date_str, "%Y-%m-%d")
    check_out = datetime.strptime(check_out_date_str, "%Y-%m-%d")
    booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d")

    db_cursor.execute(
        "SELECT PeakRate, OffPeakRate FROM Rate WHERE HotelID = %s AND RoomTypeID = %s",
        (hotel_id, room_type_id)
    )
    result = db_cursor.fetchone()
    if not result:
        raise Exception("Rate not found for this hotel and room type")

    peak_rate, off_peak_rate = map(Decimal, result)

    peak_months = [4, 5, 6, 7, 8, 11, 12]
    is_peak = check_in.month in peak_months
    daily_rate = peak_rate if is_peak else off_peak_rate

    if room_type_id == 2:
        daily_rate *= Decimal("1.2")
        if num_guests == 2:
            daily_rate += peak_rate * Decimal("0.1")
    elif room_type_id == 3:
        daily_rate *= Decimal("1.5")

    nights = (check_out - check_in).days
    base_price = daily_rate * nights

    days_advance = (check_in - booking_date).days
    if 80 <= days_advance <= 90:
        discount = Decimal("0.3")
    elif 60 <= days_advance < 80:
        discount = Decimal("0.2")
    elif 45 <= days_advance < 60:
        discount = Decimal("0.1")
    else:
        discount = Decimal("0")

    final_price = base_price * (1 - discount)
    return base_price.quantize(Decimal("0.01")), final_price.quantize(Decimal("0.01"))

# ---------------- BOOKING HANDLING ---------------- #

@booking_bp.route('/booking', methods=['POST'])
def handle_booking_submission():
    user_id = session['user_id']
    hotel_id = int(request.form['hotel_id'])
    room_type_id = int(request.form['roomType'])
    check_in = request.form['check-in']
    check_out = request.form['check-out']
    booking_date = request.form['booking-date']
    guests = int(request.form['noOfGuests'])
    currency = "GBP"

    with get_connection() as conn:
        cursor = conn.cursor()

        original, discounted = calculate_total_price(
            check_in, check_out, booking_date, hotel_id, room_type_id, guests, cursor
        )

        cursor.execute("""
            SELECT RoomID, RoomNumber FROM Room
            WHERE HotelID = %s AND RoomTypeID = %s AND IsAvailable = 1
            LIMIT 1
        """, (hotel_id, room_type_id))
        room = cursor.fetchone()
        if not room:
            return render_template('no_rooms.html')

        room_id, room_number = room

        cursor.execute("""
            INSERT INTO Booking (UserID, HotelID, RoomTypeID, RoomID, CheckIn, CheckOut, BookingDate, NoOfGuests, TotalPrice, BookingCurrency, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, hotel_id, room_type_id, room_id, check_in, check_out, booking_date, guests, discounted, currency, 'Confirmed'))
        booking_id = cursor.lastrowid
        session['latest_booking_id'] = booking_id

        cursor.execute("UPDATE Room SET IsAvailable = 0 WHERE RoomID = %s", (room_id,))

        cursor.execute("""
            INSERT INTO Receipt (BookingID, TotalPrice, PaymentDate)
            VALUES (%s, %s, %s)
        """, (booking_id, discounted, datetime.now().date()))

        conn.commit()

    return render_template(
        'booking_success.html',
        room_number=room_number,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        total_price=discounted,
        currency=currency,
        receipt_id=booking_id,
        payment_date=datetime.now().date()
    )

# ---------------- PRICE CHECK ---------------- #

@booking_bp.route('/calculate_price')
def calculate_price():
    try:
        room_type_id = int(request.args.get("roomTypeId"))
        check_in = request.args.get("checkInDate")
        check_out = request.args.get("checkOutDate")
        guests = int(request.args.get("guests"))
        hotel_name = request.args.get("hotelName")
        booking_date = datetime.today().strftime("%Y-%m-%d")

        if not all([room_type_id, check_in, check_out, guests, hotel_name]):
            return jsonify({"error": "Missing required fields"}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT HotelID FROM Hotel WHERE HotelName = %s", (hotel_name,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"error": "Hotel not found"}), 400

            hotel_id = result[0]
            original, discounted = calculate_total_price(
                check_in, check_out, booking_date, hotel_id, room_type_id, guests, cursor
            )

            return jsonify({
                "total_price": float(original),
                "discounted_price": float(discounted)
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------- MY BOOKINGS ---------------- #

@booking_bp.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Booking WHERE UserID = %s", (user_id,))
        total = cursor.fetchone()[0]
        total_pages = (total + per_page - 1) // per_page

        cursor.execute("""
            SELECT b.BookingID, b.HotelID, b.RoomID, b.CheckIn, b.CheckOut, b.NoOfGuests, b.Status, h.HotelName
            FROM Booking b
            JOIN Hotel h ON b.HotelID = h.HotelID
            WHERE b.UserID = %s
            ORDER BY b.BookingID DESC
            LIMIT %s OFFSET %s
        """, (user_id, per_page, offset))
        bookings = cursor.fetchall()

    return render_template('my_bookings.html', bookings=bookings, page=page, total_pages=total_pages)

# ---------------- CANCELLATION ---------------- #

def calculate_cancellation_fee(booking_date, check_in, cancellation_date, total_price):
    days_before = (check_in - cancellation_date).days
    if days_before > 60:
        return 0.0
    elif 30 <= days_before <= 60:
        return total_price * 0.5
    return total_price

@booking_bp.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    booking_id = request.form.get('booking_id')
    user_id = session['user_id']

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT RoomID, CheckIn, BookingDate, TotalPrice
            FROM Booking WHERE BookingID = %s AND UserID = %s
        """, (booking_id, user_id))
        result = cursor.fetchone()
        if not result:
            return "Unauthorized or not found", 403

        room_id, check_in, booking_date, total_price = result
        check_in = datetime.strptime(str(check_in), "%Y-%m-%d")
        booking_date = datetime.strptime(str(booking_date), "%Y-%m-%d")
        today = datetime.now().date()
        fee = calculate_cancellation_fee(booking_date, check_in.date(), today, float(total_price))

        cursor.execute("UPDATE Booking SET Status = 'Cancelled' WHERE BookingID = %s", (booking_id,))
        cursor.execute("UPDATE Room SET IsAvailable = 1 WHERE RoomID = %s", (room_id,))
        cursor.execute("""
            INSERT INTO Cancellations (CancellationDate, CancellationFee, BookingID)
            VALUES (%s, %s, %s)
        """, (today, fee, booking_id))
        conn.commit()

    return redirect(url_for('booking.my_bookings'))

@booking_bp.route('/check_cancellation_fee')
def check_cancellation_fee():
    booking_id = request.args.get('booking_id')
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT CheckIn, BookingDate, TotalPrice FROM Booking WHERE BookingID = %s", (booking_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Booking not found"}), 404

        check_in, booking_date, price = row
        fee = calculate_cancellation_fee(
            datetime.strptime(str(booking_date), "%Y-%m-%d"),
            datetime.strptime(str(check_in), "%Y-%m-%d").date(),
            datetime.today().date(),
            float(price)
        )
        return jsonify({"fee": round(fee, 2)})
