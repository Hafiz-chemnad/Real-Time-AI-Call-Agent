import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load your Twilio credentials from your .env file
load_dotenv()
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

# 1. Paste your Pinggy or Ngrok URL here
NEW_WEBHOOK_URL = "https://c871-2409-40f3-101d-6b60-f182-c34e-4e1f-11e7.ngrok-free.app/twilio/inbound"

try:
    # 2. Get your active phone number
    numbers = client.incoming_phone_numbers.list(limit=1)
    
    if numbers:
        phone_number = numbers[0]
        print(f"Found phone number: {phone_number.phone_number}")
        
        # 3. Force the backend database to update the Voice URL
        updated_number = phone_number.update(
            voice_url=NEW_WEBHOOK_URL,
            voice_method="POST"
        )
        print(f"✅ SUCCESS! Webhook officially updated to: {updated_number.voice_url}")
    else:
        print("No active Twilio numbers found on this account.")

except Exception as e:
    print(f"Error updating Twilio: {e}")