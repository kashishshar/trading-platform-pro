from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import os
import requests

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Bajaj API Configuration
BAJAJ_API_BASE = "https://apitrading.bajajbroking.in/api"
BAJAJ_BRIDGE_BASE = "https://bridgelink.bajajbroking.in/api"


# ==================== DATABASE MODELS ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    bajaj_user_id = db.Column(db.String(100))
    bajaj_jwt_token = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True)
    trades = db.relationship('Trade', backref='user', lazy=True)
    portfolio = db.relationship('Portfolio', backref='user', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    order_type = db.Column(db.String(10), nullable=False)  # BUY/SELL
    order_style = db.Column(db.String(10), nullable=False)  # MARKET/LIMIT
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False)  # NEW/PLACED/EXECUTED/CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.String(36), unique=True, nullable=False)
    order_id = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    order_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'symbol', name='_user_symbol_uc'),)


# Static instruments data
INSTRUMENTS = [
    {"symbol": "RELIANCE", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 2450.50},
    {"symbol": "TCS", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 3680.25},
    {"symbol": "INFY", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 1542.75},
    {"symbol": "HDFCBANK", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 1625.30},
    {"symbol": "ICICIBANK", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 1089.60},
    {"symbol": "HINDUNILVR", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 2385.90},
    {"symbol": "BHARTIARTL", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 1544.25},
    {"symbol": "ITC", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 456.80},
    {"symbol": "SBIN", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 598.45},
    {"symbol": "KOTAKBANK", "exchange": "NSE", "instrumentType": "EQUITY", "lastTradedPrice": 1789.30}
]


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('fullName', '')
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400
    
    if len(password) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"status": "error", "message": "Email already registered"}), 400
    
    password_hash = generate_password_hash(password)
    
    new_user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "User registered successfully",
        "data": {
            "id": new_user.id,
            "email": new_user.email,
            "fullName": new_user.full_name
        }
    }), 201


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
    
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "status": "success",
        "message": "Login successful",
        "data": {
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "fullName": user.full_name
            }
        }
    }), 200


@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    return jsonify({
        "status": "success",
        "data": {
            "id": user.id,
            "email": user.email,
            "fullName": user.full_name,
            "bajajConnected": bool(user.bajaj_user_id),
            "createdAt": user.created_at.isoformat()
        }
    }), 200


@app.route('/api/v1/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Reset password (simplified - no email for demo)"""
    data = request.get_json()
    
    email = data.get('email')
    new_password = data.get('newPassword')
    
    if not email or not new_password:
        return jsonify({"status": "error", "message": "Email and new password are required"}), 400
    
    if len(new_password) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"status": "error", "message": "Email not found"}), 404
    
    # Update password
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Password reset successfully. Please login with your new password."
    }), 200


@app.route('/api/v1/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password while logged in"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    if not current_password or not new_password:
        return jsonify({"status": "error", "message": "Current and new password are required"}), 400
    
    if len(new_password) < 8:
        return jsonify({"status": "error", "message": "New password must be at least 8 characters"}), 400
    
    user = User.query.get(user_id)
    
    if not user or not check_password_hash(user.password_hash, current_password):
        return jsonify({"status": "error", "message": "Current password is incorrect"}), 401
    
    # Update password
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Password changed successfully"
    }), 200


@app.route('/api/v1/auth/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Delete user account and all associated data"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    password = data.get('password')
    
    if not password:
        return jsonify({"status": "error", "message": "Password is required to delete account"}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    # Verify password
    if not check_password_hash(user.password_hash, password):
        return jsonify({"status": "error", "message": "Incorrect password"}), 401
    
    # Delete all user data (cascade delete)
    # Orders, trades, and portfolio will be deleted automatically if set up with cascade
    # Otherwise, delete manually:
    Order.query.filter_by(user_id=user_id).delete()
    Trade.query.filter_by(user_id=user_id).delete()
    Portfolio.query.filter_by(user_id=user_id).delete()
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Account deleted successfully"
    }), 200


# ==================== TRADING ROUTES ====================

@app.route('/api/v1/instruments', methods=['GET'])
@jwt_required()
def get_instruments():
    """Get list of tradable instruments"""
    return jsonify({
        "status": "success",
        "data": INSTRUMENTS
    }), 200


@app.route('/api/v1/orders', methods=['POST'])
@jwt_required()
def place_order():
    """Place a new order"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    symbol = data.get('symbol')
    order_type = data.get('orderType')
    order_style = data.get('orderStyle')
    quantity = data.get('quantity')
    price = data.get('price')
    
    # Validations
    if not all([symbol, order_type, order_style, quantity]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    
    if order_type not in ['BUY', 'SELL']:
        return jsonify({"status": "error", "message": "orderType must be BUY or SELL"}), 400
    
    if order_style not in ['MARKET', 'LIMIT']:
        return jsonify({"status": "error", "message": "orderStyle must be MARKET or LIMIT"}), 400
    
    if quantity <= 0:
        return jsonify({"status": "error", "message": "quantity must be greater than 0"}), 400
    
    if order_style == 'LIMIT' and not price:
        return jsonify({"status": "error", "message": "price is required for LIMIT orders"}), 400
    
    # Check if symbol exists
    instrument = next((i for i in INSTRUMENTS if i['symbol'] == symbol), None)
    if not instrument:
        return jsonify({"status": "error", "message": f"Invalid symbol: {symbol}"}), 400
    
    # For SELL orders, check holdings
    if order_type == 'SELL':
        holding = Portfolio.query.filter_by(user_id=user_id, symbol=symbol).first()
        if not holding or holding.quantity < quantity:
            return jsonify({"status": "error", "message": "Insufficient holdings to sell"}), 400
    
    # Create order
    order_id = str(uuid.uuid4())
    order_price = price if order_style == 'LIMIT' else instrument['lastTradedPrice']
    
    new_order = Order(
        order_id=order_id,
        user_id=user_id,
        symbol=symbol,
        order_type=order_type,
        order_style=order_style,
        quantity=quantity,
        price=order_price,
        status='PLACED'
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    # Execute MARKET orders immediately
    if order_style == 'MARKET':
        execute_order(order_id)
    
    order = Order.query.filter_by(order_id=order_id).first()
    
    return jsonify({
        "status": "success",
        "data": {
            "orderId": order.order_id,
            "symbol": order.symbol,
            "orderType": order.order_type,
            "orderStyle": order.order_style,
            "quantity": order.quantity,
            "price": order.price,
            "status": order.status,
            "timestamp": order.created_at.isoformat()
        }
    }), 201


@app.route('/api/v1/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get all orders for current user"""
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    return jsonify({
        "status": "success",
        "data": [{
            "orderId": o.order_id,
            "symbol": o.symbol,
            "orderType": o.order_type,
            "orderStyle": o.order_style,
            "quantity": o.quantity,
            "price": o.price,
            "status": o.status,
            "timestamp": o.created_at.isoformat()
        } for o in orders]
    }), 200


@app.route('/api/v1/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order_status(order_id):
    """Get specific order status"""
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(order_id=order_id, user_id=user_id).first()
    
    if not order:
        return jsonify({"status": "error", "message": "Order not found"}), 404
    
    return jsonify({
        "status": "success",
        "data": {
            "orderId": order.order_id,
            "symbol": order.symbol,
            "orderType": order.order_type,
            "orderStyle": order.order_style,
            "quantity": order.quantity,
            "price": order.price,
            "status": order.status,
            "timestamp": order.created_at.isoformat()
        }
    }), 200


@app.route('/api/v1/trades', methods=['GET'])
@jwt_required()
def get_trades():
    """Get all trades for current user"""
    user_id = int(get_jwt_identity())
    trades = Trade.query.filter_by(user_id=user_id).order_by(Trade.executed_at.desc()).all()
    
    return jsonify({
        "status": "success",
        "data": [{
            "tradeId": t.trade_id,
            "orderId": t.order_id,
            "symbol": t.symbol,
            "orderType": t.order_type,
            "quantity": t.quantity,
            "price": t.price,
            "timestamp": t.executed_at.isoformat()
        } for t in trades]
    }), 200


@app.route('/api/v1/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    """Get current portfolio holdings"""
    user_id = int(get_jwt_identity())
    holdings = Portfolio.query.filter_by(user_id=user_id).all()
    
    portfolio_data = []
    for holding in holdings:
        instrument = next((i for i in INSTRUMENTS if i['symbol'] == holding.symbol), None)
        current_price = instrument['lastTradedPrice'] if instrument else 0
        current_value = holding.quantity * current_price
        
        portfolio_data.append({
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "averagePrice": holding.average_price,
            "currentPrice": current_price,
            "currentValue": current_value,
            "profitLoss": current_value - holding.total_cost,
            "profitLossPercent": ((current_value - holding.total_cost) / holding.total_cost * 100) if holding.total_cost > 0 else 0
        })
    
    return jsonify({
        "status": "success",
        "data": portfolio_data
    }), 200


# ==================== BAJAJ API ROUTES ====================

@app.route('/api/v1/bajaj/connect', methods=['POST'])
@jwt_required()
def connect_bajaj():
    """Connect user's Bajaj Broking account"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    bajaj_user_id = data.get('userId')
    password = data.get('password')
    dob = data.get('dateOfBirth')
    
    if not all([bajaj_user_id, password, dob]):
        return jsonify({"status": "error", "message": "All Bajaj credentials required"}), 400
    
    try:
        login_url = f"{BAJAJ_API_BASE}/user/login"
        response = requests.post(login_url, json={
            "userId": bajaj_user_id,
            "password": password,
            "dateOfBirth": dob
        }, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('statusCode') == 0:
                jwt_token = result.get('data', {}).get('token')
                
                user = User.query.get(user_id)
                user.bajaj_user_id = bajaj_user_id
                user.bajaj_jwt_token = jwt_token
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Bajaj account connected successfully"
                }), 200
            else:
                return jsonify({"status": "error", "message": "Bajaj login failed"}), 401
        else:
            return jsonify({"status": "error", "message": "Bajaj API error"}), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/bajaj/profile', methods=['GET'])
@jwt_required()
def get_bajaj_profile():
    """Get user's Bajaj profile"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user.bajaj_jwt_token:
        return jsonify({"status": "error", "message": "Bajaj account not connected"}), 400
    
    try:
        profile_url = f"{BAJAJ_BRIDGE_BASE}/user/userProfile"
        response = requests.get(profile_url, headers={
            "Authorization": f"Bearer {user.bajaj_jwt_token}"
        })
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "data": response.json().get('data', {})
            }), 200
        else:
            return jsonify({"status": "error", "message": "Failed to fetch profile"}), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== ADMIN ROUTES ====================

@app.route('/api/v1/admin/users', methods=['GET'])
def get_all_users():
    """Get all registered users (ADMIN ONLY)"""
    # Simple admin authentication - check for admin key in header
    admin_key = request.headers.get('X-Admin-Key')
    
    # Set your admin key here (change this to something secure!)
    ADMIN_KEY = os.environ.get('ADMIN_KEY', 'admin123')
    
    if admin_key != ADMIN_KEY:
        return jsonify({"status": "error", "message": "Unauthorized - Admin key required"}), 401
    
    users = User.query.all()
    
    return jsonify({
        "status": "success",
        "total_users": len(users),
        "data": [{
            "id": user.id,
            "email": user.email,
            "fullName": user.full_name,
            "passwordHash": user.password_hash,  # Show password hash to admin
            "createdAt": user.created_at.isoformat(),
            "bajajConnected": bool(user.bajaj_user_id),
            "totalOrders": len(user.orders),
            "totalTrades": len(user.trades)
        } for user in users]
    }), 200


# ==================== HELPER FUNCTIONS ====================

def execute_order(order_id):
    """Execute an order and update portfolio"""
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return
    
    # Update order status
    order.status = 'EXECUTED'
    
    # Create trade record
    trade = Trade(
        trade_id=str(uuid.uuid4()),
        order_id=order_id,
        user_id=order.user_id,
        symbol=order.symbol,
        order_type=order.order_type,
        quantity=order.quantity,
        price=order.price
    )
    db.session.add(trade)
    
    # Update portfolio
    holding = Portfolio.query.filter_by(user_id=order.user_id, symbol=order.symbol).first()
    
    if order.order_type == 'BUY':
        if holding:
            new_total_cost = holding.total_cost + (order.quantity * order.price)
            new_quantity = holding.quantity + order.quantity
            holding.quantity = new_quantity
            holding.total_cost = new_total_cost
            holding.average_price = new_total_cost / new_quantity
        else:
            holding = Portfolio(
                user_id=order.user_id,
                symbol=order.symbol,
                quantity=order.quantity,
                average_price=order.price,
                total_cost=order.quantity * order.price
            )
            db.session.add(holding)
    else:  # SELL
        if holding:
            holding.quantity -= order.quantity
            if holding.quantity == 0:
                db.session.delete(holding)
            else:
                holding.total_cost = holding.quantity * holding.average_price
    
    db.session.commit()


# ==================== SYSTEM ROUTES ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "success",
        "message": "API is running",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# ==================== INITIALIZE DATABASE ====================

with app.app_context():
    db.create_all()
    print("✅ Database initialized!")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)