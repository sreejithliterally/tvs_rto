from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2

router = APIRouter()

@router.post("/sales/create-customer")
def create_customer(customer: schemas.CustomerBase, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customer_token = str(uuid4())
    print(customer_token)
    new_customer = models.Customer(
        name=customer.name,
        phone_number=customer.phone_number,
        link_token=customer_token,
        branch_id=current_user.branch_id,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        ex_showroom_price= customer.ex_showroom_price,
        tax= customer.tax,
        onroad_price= customer.onroad_price
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    customer_link = f"http://localhost:3000/customer-form/{customer_token}"
    return {"customer_link": customer_link}


@router.get("/sales/customers", response_model=List[schemas.CustomerOut])
def get_customers_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id).all()
    return customers
