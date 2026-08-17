from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from models import AuthRequest, AuthResponse
from database import get_supabase

router = APIRouter()
supabase = get_supabase()

# Password hashing setup using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/signup", response_model=AuthResponse)
def signup(req: AuthRequest):
    if not req.department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department is required for signup"
        )
    
    # Check if user already exists
    response = supabase.table("app_users").select("*").eq("username", req.username).execute()
    if response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    hashed_pwd = get_password_hash(req.password)
    
    # Insert new user
    new_user = {
        "username": req.username,
        "password_hash": hashed_pwd,
        "department": req.department
    }
    supabase.table("app_users").insert(new_user).execute()
    
    return AuthResponse(
        message="User successfully registered",
        username=req.username,
        department=req.department
    )

@router.post("/login", response_model=AuthResponse)
def login(req: AuthRequest):
    # Fetch user
    response = supabase.table("app_users").select("*").eq("username", req.username).execute()
    users = response.data
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user = users[0]
    
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
        
    return AuthResponse(
        message="Login successful",
        username=user["username"],
        department=user["department"]
    )
