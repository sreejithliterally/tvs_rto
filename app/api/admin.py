from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, utils, database
from oauth2 import get_current_user
from schemas import UserCreate
from utils import hash

router = APIRouter()

def admin_required(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

@router.post("/create_user", response_model=schemas.UserOut)
def create_user(
    user: UserCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(admin_required)
):
    # Check if username or email already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Create new user
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash(user.password),
        role=user.role,
        branch_id=user.branch_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
