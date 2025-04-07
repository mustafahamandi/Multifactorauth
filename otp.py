# otp_utils.py
import secrets
from datetime import datetime, timedelta
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# In-memory storage for OTPs
otp_storage = {}

def generate_otp():
    """Generate a secure 6-digit OTP."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def send_otp(phone_number):
    """Send an OTP to the provided phone number and store it in memory."""
    otp = generate_otp()
    expiration_time = datetime.now() + timedelta(minutes=3)  # OTP expires in 3 minutes

    # Store OTP in memory
    otp_storage[phone_number] = {
        'otp': otp,
        'expires_at': expiration_time
    }

    # Send OTP via Twilio
    message = client.messages.create(
        body=f'Your OTP is {otp}. It will expire in 3 minutes.',
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )

    return otp

def votp(phone_number, otp):
    """Verify the OTP for the given phone number."""
    if phone_number in otp_storage:
        otp_data = otp_storage[phone_number]
        if datetime.now() <= otp_data['expires_at'] and otp_data['otp'] == otp:
            # OTP is valid
            del otp_storage[phone_number]  # Delete the OTP after verification
            return True
    return False