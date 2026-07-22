from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from datetime import datetime
import logging

app = FastAPI(
    title="SupplyPilot AI API Gateway",
    description="API Gateway for DemandSense AI - AI-Powered Decision Intelligence Platform",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Logger
logger = logging.getLogger("api-gateway")
logger.setLevel(logging.INFO)

# Dependency to get the current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # In a real implementation, you would fetch the user from the database or user service
        # For now, we return the username from the token
        return {"username": username}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Middleware to add user to request state
@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    # Skip middleware for docs and health endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health", "/"]:
        response = await call_next(request)
        return response

    # Try to get token from Authorization header
    authorization: str = request.headers.get("Authorization")
    user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username:
                user = {"username": username}
        except jwt.PyJWTError:
            pass  # Invalid token, user remains None

    # Add user to request state
    request.state.user = user

    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {
        "message": "Welcome to SupplyPilot AI API Gateway",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Example protected route
@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}, you are authenticated!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)