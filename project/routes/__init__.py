from .auth import auth_bp
from .admin import admin_bp
from .booking import booking_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(booking_bp)
