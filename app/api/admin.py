from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, utils, database, oauth2
from oauth2 import get_current_user
from schemas import BranchCreate, BranchResponse, UserCreate
from utils import hash
from database import get_db
from fastapi import Query

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(oauth2.get_current_user)]
)

def admin_required(current_user: models.User = Depends(get_current_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("/customers", response_model=List[schemas.CustomerOut])
def get_all_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    
    customers = db.query(models.Customer).all()

    if not customers:
        raise HTTPException(status_code=404, detail="No customers found.")

    return customers


@router.get("/monthly-customers", response_model=List[schemas.CustomerOut])
def get_monthly_customer_registrations(
    month: int = Query(..., ge=1, le=12), 
    year: int = Query(...), 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):

    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    
    customers = db.query(models.Customer).filter(
        models.Customer.created_at >= start_date,
        models.Customer.created_at < end_date
    ).all()

    return customers

@router.get("/sales-verified-customers", response_model=List[schemas.CustomerOut])
def get_sales_verified_customers_by_branch(branch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    
    
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    
    customers = db.query(models.Customer).filter(
        models.Customer.branch_id == branch_id,
        models.Customer.sales_verified == True
    ).all()

    if not customers:
        raise HTTPException(status_code=404, detail="No sales-verified customers found.")

    return customers

@router.get("/accounts-verified-customers", response_model=List[schemas.CustomerOut])
def get_accounts_verified_customers_by_branch(branch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    
    
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    
    customers = db.query(models.Customer).filter(
        models.Customer.branch_id == branch_id,
        models.Customer.accounts_verified == True
    ).all()

    if not customers:
        raise HTTPException(status_code=404, detail="No accounts-verified customers found.")

    return customers

@router.get("/rto-verified-customers", response_model=List[schemas.CustomerOut])
def get_rto_verified_customers_by_branch(branch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    
    
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    
    customers = db.query(models.Customer).join(models.VerificationLog).filter(
        models.Customer.branch_id == branch_id,
        models.VerificationLog.action == "rto_approved"
    ).all()

    if not customers:
        raise HTTPException(status_code=404, detail="No RTO-verified customers found.")

    return customers



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
        "role_name": role_name  
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




@router.get("/total-branch-customers/{branch_id}", response_model=schemas.CustomerListResponse)
def get_user_by_id(branch_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(admin_required)):
    customers = db.query(models.Customer).filter(models.Customer.branch_id == branch_id).all()
    
   
    customer_data = [schemas.CustomerOut.from_orm(customer) for customer in customers]
    return schemas.CustomerListResponse(customers=customer_data)
