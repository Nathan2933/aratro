#!/usr/bin/env python3
"""
Test script for sending emails with Gmail credentials.
This script will prompt for Gmail credentials and test sending an email.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import sys

def test_gmail_credentials(sender_email, sender_password, recipient_email=None):
    """Test Gmail credentials by sending a test email"""
    if not recipient_email:
        recipient_email = sender_email  # Send to self if no recipient specified
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Aratro Email Test"
    
    # Create HTML content
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h1 style="color: #2d6b45;">Aratro Email Test</h1>
            <p>This is a test email to verify that your Gmail credentials are working correctly.</p>
            <p>If you received this email, your credentials are valid and can be used with the Aratro application.</p>
        </div>
    </body>
    </html>
    """
    
    # Attach HTML content
    message.attach(MIMEText(html, "html"))
    
    try:
        print(f"Attempting to send email to {recipient_email}...")
        
        # Create SMTP session
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Secure the connection
        
        # Login to sender email
        server.login(sender_email, sender_password)
        
        # Send email
        server.send_message(message)
        
        # Close connection
        server.quit()
        
        print(f"Email sent successfully to {recipient_email}")
        print("\nYour Gmail credentials are working correctly!")
        print("You can update the email_utils.py file with these credentials.")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {str(e)}")
        print("\nIf using Gmail with 2FA enabled, you need to use an App Password.")
        print("See: https://support.google.com/accounts/answer/185833")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("Aratro Gmail Credentials Test")
    print("=" * 60)
    print("This script will test your Gmail credentials by sending a test email.")
    print("If you have 2FA enabled on your Gmail account, you'll need to use an App Password.")
    print("See: https://support.google.com/accounts/answer/185833")
    print("=" * 60)
    
    sender_email = input("Enter your Gmail address: ")
    if not sender_email or '@' not in sender_email:
        print("Invalid email address.")
        return
    
    sender_password = getpass.getpass("Enter your password or App Password: ")
    if not sender_password:
        print("Password cannot be empty.")
        return
    
    recipient_email = input("Enter recipient email (leave blank to send to yourself): ")
    if not recipient_email:
        recipient_email = sender_email
    
    success = test_gmail_credentials(sender_email, sender_password, recipient_email)
    
    if success:
        # Offer to update email_utils.py
        update = input("\nWould you like to update email_utils.py with these credentials? (y/n): ")
        if update.lower() == 'y':
            try:
                with open('email_utils.py', 'r') as f:
                    content = f.read()
                
                # Replace the sender_email and sender_password
                content = content.replace('sender_email = "aratrocorp@gmail.com"', f'sender_email = "{sender_email}"')
                content = content.replace('sender_password = "naathadaleo"', f'sender_password = "{sender_password}"')
                
                with open('email_utils.py', 'w') as f:
                    f.write(content)
                
                print("email_utils.py has been updated with your credentials.")
            except Exception as e:
                print(f"Failed to update email_utils.py: {str(e)}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main() 