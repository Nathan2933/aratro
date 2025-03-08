# Aratro - Agricultural Supply Chain Management System

Aratro is a comprehensive platform designed to streamline the agricultural supply chain by connecting farmers, warehouses, and ration shops.

## Features

- **Farmer Portal**: Manage crop inventory and submit storage requests
- **Warehouse Portal**: Process storage requests and manage inventory
- **Ration Shop Portal**: Order and distribute agricultural products
- **Admin Dashboard**: Oversee all operations and approve registrations
- **SMS Notifications**: Send OTP and notifications via SMS using Twilio

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/aratro.git
   cd aratro
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URI=sqlite:///aratro.db
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password-here
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   TWILIO_ACCOUNT_SID=your-twilio-account-sid
   TWILIO_AUTH_TOKEN=your-twilio-auth-token
   TWILIO_PHONE_NUMBER=your-twilio-phone-number
   ```

### Email Configuration

For the email functionality to work properly (sending credentials to ration shop owners, etc.), you need to set up your Gmail account:

#### If you have 2-Factor Authentication enabled (recommended):

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google," select "App passwords"
3. Generate a new App Password for "Mail" and "Other (Custom name)" - name it "Aratro"
4. Copy the generated 16-character password
5. Paste it as the `EMAIL_PASSWORD` value in your `.env` file

#### If you don't have 2-Factor Authentication:

1. Go to [Less secure app access](https://myaccount.google.com/lesssecureapps)
2. Turn on "Allow less secure apps"
3. Use your regular Gmail password as the `EMAIL_PASSWORD` value in your `.env` file

**Note**: Google may still block sign-in attempts from "less secure apps." For production use, we recommend using a dedicated email service provider.

### Twilio Configuration

For SMS functionality to work properly (sending OTP codes, notifications, etc.), you need to set up a Twilio account:

1. Sign up for a Twilio account at [Twilio](https://www.twilio.com/)
2. Once registered, navigate to your [Twilio Console Dashboard](https://www.twilio.com/console)
3. Find your Account SID and Auth Token
4. Purchase a Twilio phone number or use the trial number provided
5. Add these details to your `.env` file:
   ```
   TWILIO_ACCOUNT_SID=your-account-sid
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_PHONE_NUMBER=your-twilio-phone-number
   ```

To test if your Twilio integration is working correctly, run:
```
python test_sms.py +1234567890
```
Replace `+1234567890` with your actual phone number (including country code).

### Running the Application

1. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

2. Start the application:
   ```
   python app.py
   ```

3. Access the application at `http://localhost:5000`

### Default Admin Credentials

- Email: admin@aratro.com
- Password: admin123

## License

This project is licensed under the MIT License - see the LICENSE file for details.
