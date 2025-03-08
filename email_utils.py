import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from flask import current_app
import logging
import ssl
import traceback
import random
import string
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logging.basicConfig(level=logging.DEBUG,  # Change to DEBUG for more detailed logs
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('email_utils')

def send_email(recipient_email, subject, html_content):
    """
    Generic function to send emails
    
    Args:
        recipient_email (str): The email address of the recipient
        subject (str): Email subject
        html_content (str): HTML content of the email
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get email credentials from environment variables or use defaults for development
    sender_email = os.environ.get("EMAIL_USER", "aratrocorp@gmail.com")
    sender_password = os.environ.get("EMAIL_PASSWORD", "")
    
    logger.debug(f"Email configuration: USER={sender_email}, PASSWORD={'*' * len(sender_password) if sender_password else 'NOT SET'}")
    
    if not sender_email or not sender_password:
        logger.error("Email credentials are not properly configured. Check your .env file or environment variables.")
        return False
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    
    # Attach HTML content
    message.attach(MIMEText(html_content, "html"))
    
    try:
        logger.info(f"Attempting to send email to {recipient_email}")
        logger.debug(f"Email subject: {subject}")
        
        # Create SMTP session with SSL context
        logger.debug("Creating SSL context")
        context = ssl.create_default_context()
        
        # Connect to Gmail's SMTP server
        logger.debug("Connecting to Gmail SMTP server (smtp.gmail.com:465)")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            # Login to sender email
            logger.debug(f"Attempting to login with user: {sender_email}")
            server.login(sender_email, sender_password)
            logger.debug("Login successful")
            
            # Send email
            logger.debug("Sending email message")
            server.send_message(message)
            logger.debug("Email sent successfully")
            
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        logger.error("If using Gmail, make sure you're using an App Password if 2FA is enabled")
        logger.error("Go to https://myaccount.google.com/apppasswords to generate an App Password")
        logger.error("Make sure there are no extra spaces or characters in your password")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return False

def send_credentials_email(recipient_email, shop_name, unique_id, password):
    """
    Send an email with the unique ID and password to a ration shop owner
    
    Args:
        recipient_email (str): The email address of the recipient
        shop_name (str): The name of the ration shop
        unique_id (str): The unique ID for login
        password (str): The temporary password
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    logger.info(f"Preparing to send credentials email to {recipient_email} for shop: {shop_name}")
    subject = "Your Aratro Ration Shop Credentials"
    
    # Create HTML content
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #2d6b45;">Aratro Ration Shop Portal</h1>
            </div>
            
            <p>Dear <strong>{shop_name}</strong>,</p>
            
            <p>Your ration shop registration has been approved. You can now access the Aratro Ration Shop Portal using the following credentials:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Unique ID:</strong> {unique_id}</p>
                <p><strong>Temporary Password:</strong> {password}</p>
            </div>
            
            <p>Please log in at <a href="http://localhost:5000/auth/ration/login">Aratro Ration Shop Portal</a> using these credentials. You will be prompted to change your password upon first login.</p>
            
            <p>For security reasons, please do not share these credentials with anyone.</p>
            
            <p>If you have any questions or need assistance, please contact our support team.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #777; font-size: 12px;">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 Aratro Corporation. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient_email, subject, html)

def send_rejection_email(recipient_email, reason):
    """
    Send an email notifying the ration shop owner that their registration was rejected
    
    Args:
        recipient_email (str): The email address of the recipient
        reason (str): The reason for rejection
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    logger.info(f"Preparing to send rejection email to {recipient_email}")
    subject = "Aratro Ration Shop Registration Status"
    
    # Create HTML content
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #2d6b45;">Aratro Ration Shop Portal</h1>
            </div>
            
            <p>Dear Applicant,</p>
            
            <p>We regret to inform you that your ration shop registration application has been denied.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Reason for denial:</strong></p>
                <p>{reason if reason else "No specific reason provided."}</p>
            </div>
            
            <p>If you believe this decision was made in error or if you would like to submit a new application with updated information, please contact our support team.</p>
            
            <p>Thank you for your interest in the Aratro platform.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #777; font-size: 12px;">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 Aratro Corporation. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient_email, subject, html)

def send_password_reset_email(recipient_email, unique_id, new_password):
    """
    Send an email with the new password to a ration shop owner
    
    Args:
        recipient_email (str): The email address of the recipient
        unique_id (str): The unique ID for login
        new_password (str): The new password
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    logger.info(f"Preparing to send password reset email to {recipient_email}")
    subject = "Your Aratro Ration Shop Password Has Been Reset"
    
    # Create HTML content
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #2d6b45;">Aratro Ration Shop Portal</h1>
            </div>
            
            <p>Dear Ration Shop Owner,</p>
            
            <p>Your password for the Aratro Ration Shop Portal has been reset by an administrator.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Unique ID:</strong> {unique_id}</p>
                <p><strong>New Password:</strong> {new_password}</p>
            </div>
            
            <p>Please log in at <a href="http://localhost:5000/auth/ration/login">Aratro Ration Shop Portal</a> using these credentials.</p>
            
            <p>For security reasons, please do not share these credentials with anyone and consider changing your password after logging in.</p>
            
            <p>If you did not request this password reset or if you have any questions, please contact our support team immediately.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #777; font-size: 12px;">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 Aratro Corporation. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient_email, subject, html)

def generate_otp(length=6):
    """
    Generate a random OTP code of specified length
    
    Args:
        length (int): Length of the OTP code (default: 6)
    
    Returns:
        str: The generated OTP code
    """
    return ''.join(random.choices(string.digits, k=length))

def send_otp_via_email(recipient_email, phone_number, otp_code):
    """
    Send an OTP code via email (simulating SMS)
    
    Args:
        recipient_email (str): The email address of the recipient
        phone_number (str): The phone number of the recipient
        otp_code (str): The OTP code to send
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    logger.info(f"Preparing to send OTP to {phone_number} via email {recipient_email}")
    subject = "Your Aratro Password Reset OTP"
    
    # Create HTML content
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #2d6b45;">Aratro Password Reset</h1>
            </div>
            
            <p>Dear User,</p>
            
            <p>You have requested to reset your password for your Aratro account.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <p style="font-size: 24px; font-weight: bold;">{otp_code}</p>
                <p>This is your One-Time Password (OTP) for password reset.</p>
            </div>
            
            <p>This OTP is valid for 10 minutes. If you did not request this password reset, please ignore this message.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #777; font-size: 12px;">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 Aratro Corporation. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient_email, subject, html)

def send_otp_via_sms(phone_number, otp_code):
    """
    Send an OTP code via SMS using Twilio
    
    Args:
        phone_number (str): The phone number of the recipient
        otp_code (str): The OTP code to send
    
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # Check if Twilio credentials are configured
    if not account_sid or not auth_token or not twilio_phone:
        logger.error("Twilio credentials are not properly configured. Check your .env file or environment variables.")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Format the message
        message_body = f"Your Aratro verification code is: {otp_code}. This code will expire in 10 minutes."
        
        # Ensure phone number is in E.164 format (e.g., +1234567890)
        if not phone_number.startswith('+'):
            # If no country code, assume India (+91) as default
            # Adjust this logic based on your user base
            if phone_number.startswith('0'):
                phone_number = '+91' + phone_number[1:]
            else:
                phone_number = '+91' + phone_number
        
        # Send the message
        message = client.messages.create(
            body=message_body,
            from_=twilio_phone,
            to=phone_number
        )
        
        logger.info(f"SMS sent successfully to {phone_number}. SID: {message.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        logger.error(traceback.format_exc())
        return False 