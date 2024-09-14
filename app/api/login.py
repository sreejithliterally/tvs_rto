from fastapi import status, HTTPException, Depends, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, utils, database, oauth2
from oauth2 import create_access_token



router = APIRouter(
    tags=['Auth']
)

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    if not utils.verify(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    access_token_user = create_access_token(data={"user_id": user.user_id})
    role_name = db.query(models.Role.role_name).filter(models.Role.role_id==user.role_id).scalar()
    response = {
        "access_token": access_token_user,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role_name": role_name,
            "branch_id": user.branch_id,
          
        }
    }

    return response