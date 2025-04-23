# Online Shopping System

A comprehensive online shopping platform built with Flask, featuring user authentication, product management, shopping cart functionality, and purchase history tracking.

## Features

### User Management
- User registration with username, ID, email, and mobile number
- Secure login system
- User authentication and session management
- Profile management

### Product Management
- Brand-based product organization
- Product details with images and descriptions
- Price range filtering
- Stock management

### Shopping Experience
- Shopping cart functionality
- Add/remove items from cart
- Quantity adjustment
- Secure checkout process

### Order Management
- Purchase history tracking
- Order status monitoring
- Bill generation and download
- Order details view

### User Interface
- Modern and responsive design
- Intuitive navigation
- Product categorization
- Search functionality

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: HTML, CSS, Bootstrap
- **Authentication**: Flask-Login
- **File Handling**: Werkzeug
- **PDF Generation**: ReportLab

## Prerequisites

- Python 3.x
- MySQL Server
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd online-shop
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the database:
- Create a MySQL database
- Update the database configuration in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/database_name'
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Access the application at `http://localhost:5000`

## Project Structure

```
online-shop/
├── app.py                  # Main application file
├── models.py              # Database models
├── forms.py               # Form definitions
├── routes.py              # Route definitions
├── static/                # Static files
│   ├── css/              # CSS stylesheets
│   ├── js/               # JavaScript files
│   └── uploads/          # Uploaded images
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── home.html         # Home page
│   ├── register.html     # Registration page
│   ├── login.html        # Login page
│   ├── cart.html         # Shopping cart
│   └── purchase_history.html  # Purchase history
└── requirements.txt       # Project dependencies
```

## Usage

1. **Registration**
   - Click "Register Now" on the home page
   - Fill in the required details
   - Submit the form to create an account

2. **Login**
   - Enter your credentials
   - Access your account dashboard

3. **Shopping**
   - Browse products by brand
   - View product details
   - Add items to cart
   - Proceed to checkout

4. **Order Management**
   - View purchase history
   - Download bills
   - Track order status

## Security Features

- Password hashing
- Session management
- Secure file uploads
- Input validation
- CSRF protection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact the development team or create an issue in the repository. 