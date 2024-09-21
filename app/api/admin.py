from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, utils, database, oauth2
from oauth2 import get_current_user
from schemas import BranchCreate, BranchResponse, UserCreate
from utils import hash
from database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(oauth2.get_current_user)]
)

def admin_required(current_user: models.User = Depends(get_current_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

@router.post("/create_user", response_model=schemas.UserOut)
def create_user(
    user: UserCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(admin_required)
):
    existing_user = db.query(models.User).filter(
         (models.User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Create new user
    new_user = models.User(
        first_name=user.first_name,
        last_name = user.last_name,
        email=user.email,
        hashed_password=hash(user.password),
        role_id=user.role_id,
        branch_id=user.branch_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    role_name = db.query(models.Role.role_name).filter(models.Role.role_id == new_user.role_id).scalar()

    response = {
        "user_id": new_user.user_id,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "email": new_user.email,
        "branch_id": new_user.branch_id,
        "role_name": role_name  # Add role_name to the response
    }
    return response





@router.get("/branches/{branch_id}/{role_id}")
def get_employees(branch_id: int, role_id:int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    employees_list = db.query(models.User).filter(models.User.branch_id == branch_id,
                                                  models.User.role_id== role_id).all()


    return employees_list

@router.get("/users", response_model=List[schemas.UserOut])
def get_all_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(admin_required)):
    users = db.query(models.User).all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found.")

    user_list = []
    for user in users:
        role_name = db.query(models.Role.role_name).filter(models.Role.role_id == user.role_id).scalar()
        user_list.append({
            "user_id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "branch_id": user.branch_id,
            "role_name": role_name
        })

    return user_list

@router.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(admin_required)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    role_name = db.query(models.Role.role_name).filter(models.Role.role_id == user.role_id).scalar()

    return {
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "branch_id": user.branch_id,
        "role_name": role_name
    }

@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(admin_required)):
    user_in_db = db.query(models.User).filter(models.User.user_id == user_id).first()

    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")

    user_in_db.first_name = user.first_name
    user_in_db.last_name = user.last_name
    user_in_db.email = user.email
    user_in_db.role_id = user.role_id
    user_in_db.branch_id = user.branch_id

    db.commit()
    db.refresh(user_in_db)

    role_name = db.query(models.Role.role_name).filter(models.Role.role_id == user_in_db.role_id).scalar()

    return {
        "user_id": user_in_db.user_id,
        "first_name": user_in_db.first_name,
        "last_name": user_in_db.last_name,
        "email": user_in_db.email,
        "branch_id": user_in_db.branch_id,
        "role_name": role_name
    }
@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(admin_required)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    return {"detail": f"User with ID {user_id} deactivated"}



@router.post("/branches", response_model=BranchResponse)
def create_branch(branch: BranchCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(admin_required)):
    new_branch = models.Branch(
        name=branch.name,
        address=branch.address,
        phone_number=branch.phone_number,
        branch_manager=branch.branch_manager
    )
    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)

    return new_branch


@router.get("/", response_model=List[schemas.Branch])
def get_branches(db: Session = Depends(get_db)):
    branches = db.query(models.Branch).all()
    return branches


@router.get("/{branch_id}", response_model=schemas.Branch)
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return branch


@router.put("/{branch_id}", response_model=schemas.Branch)
def update_branch(branch_id: int, branch_update: schemas.BranchUpdate, db: Session = Depends(get_db)):
    branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    
    branch.name = branch_update.name
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(database.get_db)):
    branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    
  
    db.delete(branch)
    db.commit()
    return {"detail": f"Branch with ID {branch_id} deleted"}