from datetime import datetime

def calculate_total_price(check_in_date_str, check_out_date_str, booking_date_str, hotel_id, room_type_id, num_guests, db_cursor):
    """Calculate total and discounted price for a hotel booking."""
    check_in = datetime.strptime(check_in_date_str, '%Y-%m-%d')
    check_out = datetime.strptime(check_out_date_str, '%Y-%m-%d')
    booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d')

    num_nights = (check_out - check_in).days
    if num_nights <= 0:
        raise ValueError("Check-out date must be after check-in date.")

    db_cursor.execute(
        "SELECT PeakRate, OffPeakRate FROM Rate WHERE HotelID = %s AND RoomTypeID = %s",
        (hotel_id, room_type_id)
    )
    rates = db_cursor.fetchone()
    if not rates:
        raise ValueError("Rate not found for the selected hotel and room type.")
    
    peak_rate, off_peak_rate = rates
    is_peak = check_in.month in {4, 5, 6, 7, 8, 11, 12}
    base_rate = peak_rate if is_peak else off_peak_rate

    # Room type multipliers
    multiplier = 1.0
    if room_type_id == 2:
        multiplier = 1.2 + (0.1 if num_guests == 2 else 0)
    elif room_type_id == 3:
        multiplier = 1.5

    total_price = num_nights * base_rate * multiplier

    # Discount logic
    days_advance = (check_in - booking_date).days
    if days_advance >= 80:
        discount = 0.30
    elif days_advance >= 60:
        discount = 0.20
    elif days_advance >= 45:
        discount = 0.10
    else:
        discount = 0.0

    discounted_price = round(total_price * (1 - discount), 2)

    return {
        'total_price': round(total_price, 2),
        'discounted_price': discounted_price,
        'discount_percent': int(discount * 100)
    }


def apply_discounts(total_price, check_in_date):
    """Apply basic discount based on days in advance."""
    if isinstance(check_in_date, str):
        check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d')

    days_advance = (check_in_date - datetime.now()).days
    if days_advance >= 30:
        return round(total_price * 0.90, 2)
    elif days_advance >= 15:
        return round(total_price * 0.95, 2)
    return round(total_price, 2)


def calculate_cancellation_fee(booking_date, cancellation_date, total_price):
    """Determine cancellation fee based on time difference from booking."""
    if isinstance(booking_date, str):
        booking_date = datetime.strptime(booking_date, '%Y-%m-%d')
    if isinstance(cancellation_date, str):
        cancellation_date = datetime.strptime(cancellation_date, '%Y-%m-%d')

    days_diff = (cancellation_date - booking_date).days
    if days_diff >= 60:
        return 0.0
    elif 30 <= days_diff < 60:
        return round(min(total_price * 0.5, total_price), 2)
    return round(total_price, 2)
