# app/core/security.py

from fastapi import Request, HTTPException, status
from twilio.request_validator import RequestValidator
from app.core.config import settings

async def verify_twilio_signature(request: Request) -> bool:
    """
    Validates that incoming webhook requests genuinely originate from Twilio.
    Accounts for ngrok and reverse proxies using X-Forwarded-Proto and X-Forwarded-Host.
    """
    # Bypass verification if explicitly disabled in local testing/development
    if getattr(settings, "BYPASS_TWILIO_SIGNATURE", False):
        return True

    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Twilio Auth Token is not configured on the server."
        )

    validator = RequestValidator(auth_token)
    
    # Extract the signature header
    twilio_signature = request.headers.get("X-Twilio-Signature", "")

    # Handle proxy headers for ngrok / cloud deployment
    forwarded_proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    forwarded_host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    
    # Reconstruct the exact absolute URL Twilio used to sign the request
    # Include query parameters if any exist
    path_with_query = request.url.path
    if request.url.query:
        path_with_query += f"?{request.url.query}"
        
    target_url = f"{forwarded_proto}://{forwarded_host}{path_with_query}"

    # Extract form data (Twilio sends application/x-www-form-urlencoded for webhooks)
    form_data = await request.form()
    params = dict(form_data)

    # Validate via Twilio's official library
    is_valid = validator.validate(target_url, params, twilio_signature)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature. Request blocked."
        )

    return True