import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

def make_outbound_call():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        print("❌ Error: Missing Twilio credentials in your .env file.")
        return

    client = Client(account_sid, auth_token)

    print("\n--- 📞 Outbound Call Tester ---")
    to_number = input("Enter YOUR phone number (with country code, e.g., +919876543210): ").strip()
    
    # Get the LocalTunnel or Ngrok URL from the user
    tunnel_url = input("Enter your active tunnel URL (e.g., https://my-tunnel.loca.lt): ").strip()
    if tunnel_url.endswith("/"):
        tunnel_url = tunnel_url[:-1]

    webhook_url = f"{tunnel_url}/twilio/inbound/11111111-1111-1111-1111-111111111111" # Change /incoming-call if your FastAPI route is different
    
    print(f"\n🚀 Initiating call...")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"Webhook URL: {webhook_url}")

    try:
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=webhook_url,
            method="POST",
            record=True,
        )
        print(f"\n✅ Call successfully triggered! (SID: {call.sid})")
        print("📱 Your phone should be ringing in a few seconds. Pick it up to start the AI pipeline!")
    except Exception as e:
        print(f"\n❌ Failed to trigger call: {e}")
        print("\nNote: If you are on a Twilio Trial account, ensure the destination number is 'Verified' in your Twilio Console, and Geographic Permissions are enabled for your country.")

if __name__ == "__main__":
    make_outbound_call()