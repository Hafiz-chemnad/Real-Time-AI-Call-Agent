from twilio.rest import Client

# Your Twilio Credentials
account_sid = 'AC2307f64216ff69bc8e661111295ecd42'
auth_token = '2886f512c0e25e17825c2a8ddc84f5a1'

client = Client(account_sid, auth_token)

# Trigger the phone call
call = client.calls.create(
    to='+917994134764',     # <-- PUT YOUR VERIFIED PHONE NUMBER HERE (Keep the +91)
    from_='+17754025976',   # Your Twilio Trial Number
    url='https://6052-202-141-43-164.ngrok-free.app/twilio/inbound/11111111-1111-1111-1111-111111111111',
    method='POST',
    record=True             # This will record the call in your Twilio logs
)

print(f"Ringing your phone! Call SID: {call.sid}")