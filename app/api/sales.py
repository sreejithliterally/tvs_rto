from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
from schemas import CustomerResponse , CustomerUpdate, CustomerUpdatesales

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
    dependencies=[Depends(oauth2.get_current_user)]
)

@router.post("/create-customer")
def create_customer(customer: schemas.CustomerBase, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customer_token = str(uuid4())
    print(customer_token)
    new_customer = models.Customer(
        name=customer.name,
        phone_number=customer.phone_number,
        alternate_phone_number = customer.alternate_phone_number,
        link_token=customer_token,
        branch_id=current_user.branch_id,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        ex_showroom_price= customer.ex_showroom_price,
        tax= customer.tax,
        insurance = customer.insurance,
        tp_registration = customer.tp_registration,
        man_accessories = customer.man_accessories,
        optional_accessories = customer.optional_accessories,
        total_price = customer.total_price,
        booking = customer.booking,
        finance_amount = customer.finance_amount,
        sales_executive_id = current_user.user_id,
        finance_id=customer.finance_id if customer.finance_id else None

    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    customer_link = f"http://localhost:3000/customer-form/{customer_token}"
    return {"customer_link": customer_link}

@router.post("/verify/{customer_id}")
def verify_customer_sales(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Ensure the user is a sales executive (role_id == 2 for sales executive)
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Retrieve the customer by ID
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Update the customer verification status for sales
    customer.sales_verified = True
    
    # Log the verification action in the VerificationLog table
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="sales_verified"
    )
    
    db.add(verification_log)
    db.commit()

    return {"message": "Customer sales verification completed."}


@router.get("/customers", response_model=List[schemas.CustomerOut])
def get_customers_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id).all()

    #will return the customers' data relevant to the sales executive
    customer_data = [
        {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "address": customer.address,
            "phone_number": customer.phone_number,
            "status": customer.status,
            "branch_id": customer.branch_id,
            "photo_adhaar_front":customer.photo_adhaar_front,
            "photo_adhaar_back":customer.photo_adhaar_back,
            "photo_passport":customer.photo_passport,
            "sales_verified": customer.sales_verified,
            "accounts_verified": customer.accounts_verified,
            "vehicle_name": customer.vehicle_name,
            "vehicle_variant": customer.vehicle_variant,
            "ex_showroom_price": customer.ex_showroom_price,
            "tax": customer.tax,
            "onroad_price": customer.onroad_price,
        }
        for customer in customers
    ]
    return customer_data


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, update_data: CustomerUpdatesales, db: Session = Depends(database.get_db)):
    # Fetch the customer from the database
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Update the customer fields with the provided data
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)

    return customer




@router.get("/customers/count")
def get_customer_count_for_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    total_customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id).count()
    
    total_pending_customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.status=="pending").count()
    total_submitted_customers = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.status=="submitted").count()
    
    
    
    return {"total_count":total_customers,
            "total_pending": total_pending_customers,
            "total_submitted": total_submitted_customers
            }


@router.get("/customer-verification/count")
def customer_review_count_sales_executive(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    review_pending = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.sales_verified==False).count()
    review_done = db.query(models.Customer).filter(models.Customer.branch_id == current_user.branch_id,
                                                 models.Customer.sales_executive_id== current_user.user_id,
                                                 models.Customer.sales_verified==True).count()
    return {
        "reviews pending":review_pending,
        "reviews Done":review_done
    }