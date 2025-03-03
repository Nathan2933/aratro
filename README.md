# Supply Chain Management System

A Flask-based web application that connects farmers, warehouse managers, and ration shop managers in a streamlined supply chain system..

## Project Structure
```
supply_chain/
├── app.py              # Main application file
├── models.py           # Database models
├── routes.py           # Route handlers
├── requirements.txt    # Project dependencies
├── static/
│   └── css/
│       └── style.css  # Custom styles
└── templates/
    ├── base.html      # Base template
    ├── index.html     # Landing page
    ├── login.html     # Login page
    ├── register.html  # Registration page
    ├── farmer_dashboard.html
    ├── warehouse_dashboard.html
    └── ration_dashboard.html
```

## Features

1. **User Authentication**
   - Registration with role selection (Farmer/Warehouse/Ration Shop)
   - Login/Logout functionality
   - Role-based access control

2. **Farmer Dashboard**
   - View stock requests from warehouses
   - View nearby warehouses and their storage capacity
   - Approve/Reject stock requests

3. **Warehouse Dashboard**
   - Update storage capacity and available space
   - Manage stock inventory
   - Track stock from farmers
   - Update stock quantities

4. **Ration Shop Dashboard**
   - Request stocks from warehouses
   - View available warehouses and their stocks
   - Track request status

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Database Schema

The application uses SQLite3 for data storage with the following models:

- User: Stores user authentication details and role
- Farmer: Stores farmer-specific information
- Warehouse: Manages warehouse details and capacity
- RationShop: Stores ration shop information
- Stock: Tracks stock items and their status
- StockRequest: Manages stock requests between entities

## Security Features

- Password hashing using Werkzeug
- Flask-Login for session management
- CSRF protection with Flask-WTF
- Role-based access control

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
