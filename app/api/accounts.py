from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models , database , oauth2

router = APIRouter()



@router.post("/verify/accounts/{customer_id}")
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
