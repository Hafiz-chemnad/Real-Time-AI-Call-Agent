import uuid
from fastapi import HTTPException, Path
from app.db.session import get_db

# 1. Database Dependency
# We import get_db directly from session.py so all your API routes can cleanly import it from here.
__all__ = ["get_db", "get_target_business"]

# 2. Business Identification & Security Placeholder
async def get_target_business(business_id: uuid.UUID = Path(...)) -> uuid.UUID:
    """
    Reusable helper to extract and validate the business_id from the API URL path.
    
    NOTE FOR LATER: When Supabase Authentication is fully wired up, this exact 
    function is where you will check the user's JWT token to ensure they actually 
    own the business_id they are trying to modify!
    """
    if not business_id:
        raise HTTPException(status_code=400, detail="Business ID is missing from the request.")
    
    return business_id