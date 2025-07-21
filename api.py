from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from validator import validate_email_address_custom

app = FastAPI()

class EmailRequest(BaseModel):
    email: str

@app.post("/validate_email")
async def validate_email(request: EmailRequest):
    try:
        result = validate_email_address_custom(request.email)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# For Vercel compatibility
# vercel-python looks for a variable named "app"
