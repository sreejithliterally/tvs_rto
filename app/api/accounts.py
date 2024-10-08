from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, database, oauth2, schemas

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    dependencies=[Depends(oauth2.get_current_user)]
)

# Helper function to check if user has the accounts role
def is_user_in_accounts_role(user: models.User):
    if user.role_id != 3:  # Assuming role_id 3 is for accounts role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )

@router.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_accounts_role(current_user)
    
    # Fetch the customer by ID and ensure they belong to the same branch as the logged-in accounts person
    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id,
        models.Customer.branch_id == current_user.branch_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or not authorized to view this customer.")
    
    return customer

@router.post("/verify/{customer_id}")
def verify_customer_by_accounts(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 3:  
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    customer.accounts_verified = True
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="accounts_verified"
    )
    
    db.add(verification_log)
    db.commit()

    return {"message": "Accounts verification completed."}

@router.get("/customers", response_model=List[schemas.CustomerOut])
def get_customers_for_branch(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_accounts_role(current_user)
    
    # Fetch customers only from the user's branch where sales are verified
    customers = db.query(models.Customer).filter(
        models.Customer.branch_id == current_user.branch_id,
        models.Customer.sales_verified == True
    ).all()
    
    return customers

@router.put("/customers/{customer_id}", response_model=schemas.CustomerOut)
def update_customer_accounts(
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_accounts_role(current_user)
    
    # Find the customer in the user's branch
    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id,
        models.Customer.branch_id == current_user.branch_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if customer_update.accounts_verified is not None:
        customer.accounts_verified = customer_update.accounts_verified
    
    if customer_update.status is not None:
        customer.status = customer_update.status
    
    db.commit()
    db.refresh(customer)
    
    return customer
