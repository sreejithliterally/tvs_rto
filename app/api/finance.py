from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
from schemas import CustomerResponse , CustomerUpdate, CustomerUpdatesales

router = APIRouter(
    prefix="/finances",
    tags=["Finance"],
    dependencies=[Depends(oauth2.get_current_user)]
)


@router.post("/new-finance")
def create_finance(finance: schemas.FinanceCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    new_finance = models.FinanceOption(
        company_name=finance.company_name,
        details = finance.details
        )
    db.add(new_finance)
    db.commit()
    db.refresh(new_finance)
    
    return {"new finance option added succesfully"}

@router.put("/update-finance/{finance_id}")
def update_finance(
    finance_id: int,
    finance: schemas.FinanceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Check if the user is an admin
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Fetch the finance option to be updated
    finance_option = db.query(models.FinanceOption).filter(models.FinanceOption.finance_id == finance_id).first()

    # If finance option does not exist, return a 404 error
    if not finance_option:
        raise HTTPException(status_code=404, detail="Finance option not found.")

    # Update the finance option details
    finance_option.company_name = finance.company_name
    finance_option.details = finance.details

    db.commit()
    db.refresh(finance_option)
    
    return {"message": "Finance option updated successfully", "finance_option": finance_option}


@router.delete("/delete-finance/{finance_id}")
def delete_finance(
    finance_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Check if the user is an admin
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")

    # Fetch the finance option to be deleted
    finance_option = db.query(models.FinanceOption).filter(models.FinanceOption.finance_id == finance_id).first()

    # If finance option does not exist, return a 404 error
    if not finance_option:
        raise HTTPException(status_code=404, detail="Finance option not found.")

    # Delete the finance option
    db.delete(finance_option)
    db.commit()

    return {"message": "Finance option deleted successfully"}


@router.get("/available-finances")
def get_available_finances(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized.")
    available_options = db.query(models.FinanceOption).all()

    return{"available finances": available_options}