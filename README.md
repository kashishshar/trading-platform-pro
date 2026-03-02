# Professional Trading Platform

A full-stack trading platform with user authentication, portfolio management, and real-time market data integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)

## Screenshots

<img width="1002" height="572" alt="LoginPage" src="https://github.com/user-attachments/assets/f5bff2b0-41bc-4bec-b054-a9e35326bf8a" />
<img width="1100" height="590" alt="Dashboard with portfolio" src="https://github.com/user-attachments/assets/a1d3ab5b-4139-4d2d-8b4a-0dcbd176062f" />
<img width="1082" height="584" alt="Trades" src="https://github.com/user-attachments/assets/b6379a75-86ab-4070-a41c-0ea8eaccfd62" />
<img width="1081" height="526" alt="Admin dashboard with users" src="https://github.com/user-attachments/assets/f721a0e8-0f50-401c-b165-fcf4d296eb4b" />
<img width="563" height="586" alt="Mobile responsive view" src="https://github.com/user-attachments/assets/50785e2d-4fee-4d76-8660-f4a40d1ea034" />

## Features

### Authentication
- User Registration & Login (JWT-based)
- Forgot Password
- Change Password
- Delete Account

### Trading Features
- View Available Stocks
- Place BUY/SELL Orders (MARKET/LIMIT)
- Real-time Order Execution
- Trade History
- Portfolio Management with P&L Tracking

### Admin Features
- View All Users (Protected by Admin Key)
- User Statistics Dashboard
- Monitor Trading Activity

### API Integration
- Bajaj Broking API Integration (Optional)
- Real Market Data Support

## Tech Stack

### Backend
- **Framework:** Flask 3.0.3
- **Database:** SQLAlchemy (SQLite/PostgreSQL)
- **Authentication:** Flask-JWT-Extended
- **Security:** Werkzeug (Password Hashing)
- **CORS:** Flask-CORS

### Frontend
- **UI:** HTML5, CSS3, JavaScript
- **Styling:** Tailwind CSS
- **Design:** Responsive & Modern

### DevOps
- **Backend Hosting:** Render.com
- **Frontend Hosting:** Netlify
- **Version Control:** Git & GitHub

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kashishshar/trading-platform-pro.git
cd trading-platform-pro
```

2. **Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Mac/Linux

# Run the backend
python app.py
```

Backend will run on `http://localhost:5000`

3. **Frontend Setup**
```bash
# Simply open frontend/index.html in your browser
# OR use a local server:
cd frontend
python -m http.server 8080
```

Frontend will be available at `http://localhost:8080`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/forgot-password` - Reset password
- `POST /api/v1/auth/change-password` - Change password
- `DELETE /api/v1/auth/delete-account` - Delete account
- `GET /api/v1/auth/me` - Get current user

### Trading (Protected)
- `GET /api/v1/instruments` - List tradable instruments
- `POST /api/v1/orders` - Place new order
- `GET /api/v1/orders` - Get all orders
- `GET /api/v1/orders/:id` - Get order details
- `GET /api/v1/trades` - Get trade history
- `GET /api/v1/portfolio` - Get portfolio holdings

### Admin (Protected by Admin Key)
- `GET /api/v1/admin/users` - Get all users (requires X-Admin-Key header)

### Bajaj Integration (Optional)
- `POST /api/v1/bajaj/connect` - Connect Bajaj account
- `GET /api/v1/bajaj/profile` - Get Bajaj profile
- `GET /api/v1/bajaj/market/:symbol` - Get real market data

## Environment Variables

Create a `.env` file in the `backend` directory:
```env
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-change-in-production
DATABASE_URL=sqlite:///trading.db
PORT=5000
ADMIN_KEY=your-admin-key-change-in-production
```

** Never commit `.env` file to GitHub!**

## 🧪 Testing
```bash
cd backend
pytest tests/ -v --cov=app
```

## Documentation

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [User Guide](docs/USER_GUIDE.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Kashish Sharma**

- GitHub: [@kashishshar](https://github.com/kashishshar)
- Email: kashishsharma8124@gmail.com

##  Acknowledgments

- Bajaj Broking for API reference
- Flask community
- Tailwind CSS team

## Support

For support, email kashishsharma8124@gmail.com or create an issue in this repository.

---

⭐ If you found this project helpful, please give it a star!
