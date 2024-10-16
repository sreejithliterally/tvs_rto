from fastapi import APIRouter, Depends, HTTPException, status,Form
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import models, database, oauth2, schemas
from datetime import datetime


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


@router.get("/customers/pending", response_model=List[schemas.CustomerOut])  # Use List for multiple results
def get_pending_customers(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_accounts_role(current_user)
    
    # Query to get customers that have not been verified
    customers = db.query(models.Customer).filter(
        models.Customer.branch_id == current_user.branch_id,
        models.Customer.sales_verified==True,
        models.Customer.accounts_verified == False
    ).all()
    
    return customers



@router.get("/customers/verified", response_model=List[schemas.CustomerOut])  # Use List for multiple results
def get_verified_customers(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_accounts_role(current_user)
    
    # Query to get customers that have not been verified
    customers = db.query(models.Customer).filter(
        models.Customer.branch_id == current_user.branch_id,
        models.Customer.sales_verified == True,
        models.Customer.accounts_verified == True
    ).all()
    
    return customers


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



@router.put("/customers/{customer_id}/{finance_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    finance_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    alternate_phone_number: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),  # Assuming this is in string format (YYYY-MM-DD)
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None),
    nominee: Optional[str] = Form(None),
    relation: Optional[str] = Form(None),
    vehicle_name: Optional[str] = Form(None),
    vehicle_variant: Optional[str] = Form(None),
    vehicle_color: Optional[str] = Form(None),
    ex_showroom_price: Optional[float] = Form(None),
    tax: Optional[float] = Form(None),
    insurance: Optional[float] = Form(None),
    tp_registration: Optional[float] = Form(None),
    man_accessories: Optional[float] = Form(None),
    optional_accessories: Optional[float] = Form(None),
    total_price: Optional[float] = Form(None),
    amount_paid: Optional[float] = Form(None),
    finance_amount: Optional[float] =Form(None),
    vehicle_number: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_accounts_role(current_user)
    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Update fields if values are provided
    if first_name is not None:
        customer.first_name = first_name
    if last_name is not None:
        customer.last_name = last_name
    if phone_number is not None:
        customer.phone_number = phone_number
    if alternate_phone_number is not None:
        customer.alternate_phone_number = alternate_phone_number
    if dob is not None:
        try:
            customer.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    if email is not None:
        customer.email = email
    if address is not None:
        customer.address = address
    if pin_code is not None:
        customer.pin_code = pin_code
    if nominee is not None:
        customer.nominee = nominee
    if relation is not None:
        customer.relation = relation
    if vehicle_name is not None:
        customer.vehicle_name = vehicle_name
    if vehicle_variant is not None:
        customer.vehicle_variant = vehicle_variant
    if vehicle_color is not None:
        customer.vehicle_color = vehicle_color
    if ex_showroom_price is not None:
        customer.ex_showroom_price = Decimal(str(ex_showroom_price))
    if tax is not None:
        customer.tax = Decimal(str(tax))
    if insurance is not None:
        customer.insurance = Decimal(str(insurance))
    if tp_registration is not None:
        customer.tp_registration = Decimal(str(tp_registration))
    if man_accessories is not None:
        customer.man_accessories = Decimal(str(man_accessories))
    if optional_accessories is not None:
        customer.optional_accessories = Decimal(str(optional_accessories))

    if amount_paid is not None:
        amount_paid_decimal = Decimal(str(amount_paid))
        customer.amount_paid = amount_paid_decimal

        customer.balance_amount = customer.total_price - amount_paid_decimal
    if vehicle_number is not None:
        customer.vehicle_number = vehicle_number

    if finance_id is not None:
        customer.finance_id = finance_id
    total_price = (
        ex_showroom_price +
        tax +
        insurance +
        tp_registration +
        man_accessories +
        optional_accessories
    )

    if finance_amount is not None:
        finance_amount_decimal = Decimal(str(finance_amount))
        customer.finance_amount = finance_amount_decimal
        balance_amount = total_price - amount_paid - finance_amount
    else:
        balance_amount = total_price-amount_paid

        # Update balance amount based on finance
   
    customer.total_price = total_price
    customer.balance_amount = balance_amount


    db.commit()
    db.refresh(customer)

    full_name = f"{customer.first_name} {customer.last_name}"
    return schemas.CustomerResponse(
        customer_id=customer.customer_id,
        name=full_name,
        phone_number=customer.phone_number,
        address=customer.address,
        email=customer.email,
        vehicle_name=customer.vehicle_name,
        vehicle_variant=customer.vehicle_variant,
        vehicle_color=customer.vehicle_color,
        sales_verified=customer.sales_verified,
        accounts_verified=customer.accounts_verified,
        rto_verified=customer.rto_verified,
        registered=customer.registered,
        status=customer.status,
        created_at=customer.created_at,
        amount_paid=customer.amount_paid,
        balance_amount=customer.balance_amount
    )