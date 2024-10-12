from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
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
    
    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id,
        models.Customer.branch_id == current_user.branch_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or not authorized to view this customer.")
    
    return customer

@router.post("/verify/{customer_id}")
def verify_customer_by_accounts(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_accounts_role(current_user)
    
    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    # Check if finance is approved and update the balance amount accordingly
    if customer.finance_amount and customer.finance_amount > 0:
        balance_amount = customer.total_price - customer.amount_paid - customer.finance_amount
        customer.balance_amount = balance_amount
    
    customer.accounts_verified = True
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="accounts_verified"
    )
    
    db.add(verification_log)
    db.commit()

    return {"message": "Accounts verification completed and balance amount updated based on finance approval."}

@router.put("/customers/{customer_id}/finance", response_model=schemas.CustomerOut)
def update_finance_details(
    customer_id: int,
    finance_id: Optional[int],
    finance_amount: Optional[float],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_accounts_role(current_user)
    
    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == customer_id,
        models.Customer.branch_id == current_user.branch_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if finance_id is not None:
        customer.finance_id = finance_id

    if finance_amount is not None:
        finance_amount_decimal = Decimal(str(finance_amount))
        customer.finance_amount = finance_amount_decimal

        # Update balance amount based on finance
        customer.balance_amount = customer.total_price - customer.amount_paid - finance_amount_decimal
    
    db.commit()
    db.refresh(customer)
    
    return customer

