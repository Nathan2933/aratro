"""
Test script for Twilio SMS integration

This script tests the SMS sending functionality using Twilio.
Before running this script:
1. Make sure you have set up your Twilio credentials in the .env file
2. Install the required packages: pip install -r requirements.txt
3. Run this script: python test_sms.py <phone_number>
   Replace <phone_number> with the phone number to send the test SMS to (e.g., +1234567890)
"""

import os
import sys
import logging
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_sms')

def test_twilio_sms(phone_number):
    """
    Test sending an SMS using Twilio
    
    Args:
        phone_number (str): The phone number to send the test SMS to
    
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # Check if Twilio credentials are configured
    if not account_sid or not auth_token or not twilio_phone:
        logger.error("Twilio credentials are not properly configured. Check your .env file.")
        logger.error("Make sure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER are set.")
        return False
    
    # Ensure phone number is in E.164 format (e.g., +1234567890)
    if not phone_number.startswith('+'):
        # If no country code, assume India (+91) as default
        if phone_number.startswith('0'):
            phone_number = '+91' + phone_number[1:]
        else:
            phone_number = '+91' + phone_number
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Format the message
        message_body = "This is a test message from Aratro. If you received this, the Twilio integration is working correctly!"
        
        logger.info(f"Sending test SMS to {phone_number}...")
        
        # Send the message
        message = client.messages.create(
            body=message_body,
            from_=twilio_phone,
            to=phone_number
        )
        
        logger.info(f"SMS sent successfully! SID: {message.sid}")
        logger.info("If you received the message, the Twilio integration is working correctly.")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        if "is not a valid phone number" in str(e):
            logger.error(f"The phone number {phone_number} is not valid. Make sure it's in E.164 format (e.g., +1234567890).")
        elif "not a valid Twilio phone number" in str(e):
            logger.error(f"The Twilio phone number {twilio_phone} is not valid. Check your TWILIO_PHONE_NUMBER in .env.")
        elif "authenticate" in str(e):
            logger.error("Authentication failed. Check your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env.")
        return False
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_sms.py <phone_number>")
        print("Example: python test_sms.py +1234567890")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    test_twilio_sms(phone_number) 