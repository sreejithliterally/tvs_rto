from io import BytesIO
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse

from typing import List, Optional
from sqlalchemy.orm import Session
import models, schemas, database, oauth2
from datetime import datetime
import utils
import uuid
import zipfile
from fastapi.responses import StreamingResponse
from botocore.exceptions import ClientError
import io
import requests


router = APIRouter(
    prefix="/rto",
    tags=["RTO"]
)


def is_user_in_rto_role(user: models.User):
    if user.role_id != 4:  # Assuming role_id 4 is for RTO role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )


@router.get("/verified-customers", response_model=List[schemas.CustomerOut])
def get_verified_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

   
    customers = db.query(models.Customer).filter(models.Customer.rto_verified == True).all()

    return customers


@router.post("/verify/{customer_id}")
def verify_customer_rto(customer_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

    # Retrieve the customer by ID
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Check if the customer is eligible for RTO verification
    if not (customer.sales_verified and customer.accounts_verified):
        raise HTTPException(status_code=400, detail="Customer must be sales and accounts verified before RTO verification.")

    # Update the customer's RTO verification status
    customer.rto_verified = True

    # Log the verification action in the VerificationLog table
    verification_log = models.VerificationLog(
        user_id=current_user.user_id,
        customer_id=customer.customer_id,
        action="rto_verified",
        timestamp=datetime.utcnow()
    )

    db.add(verification_log)
    db.commit()

    return {"message": "Customer RTO registration successful"}


@router.put("/customers/{customer_id}", response_model=schemas.CustomerEditedResponse)
def update_customer(
    customer_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    vehicle_number: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_user_in_rto_role(current_user)
    
    # Retrieve the customer by ID
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
    if address is not None:
        customer.address = address

    if vehicle_number is not None:
        customer.vehicle_number = vehicle_number
        customer.registered = True

    db.commit()
    db.refresh(customer)

    return customer



@router.get("/pending-customers", response_model=List[schemas.CustomerOut])
def get_pending_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)

    # Fetch customers who are eligible for RTO verification
    customers = db.query(models.Customer).filter(
        models.Customer.sales_verified == True,
        models.Customer.accounts_verified == True,
        models.Customer.rto_verified == False
    ).all()

    if not customers:
        logging.info("No customers found matching the RTO criteria.")
    else:
        logging.info(f"Found {len(customers)} customers matching RTO criteria.")

    return customers


# Endpoint to get all customers eligible for RTO verification
@router.get("/customer-list", response_model=List[schemas.CustomerOut])
def get_customers(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    is_user_in_rto_role(current_user)
    
    # Fetch customers who are sales and accounts verified but not yet RTO verified
    customers = db.query(models.Customer).filter(
        models.Customer.sales_verified == True,
        models.Customer.accounts_verified == True,
        models.Customer.rto_verified == False
    ).all()
    
    return customers





@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer_by_id(customer_id: int, db: Session = Depends(database.get_db)):


    
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or you are not authorized to view this customer.")

    return customer



def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.split('.')[-1]  # Get the file extension
    unique_name = f"{uuid.uuid4()}.{ext}"  # Create a unique filename with the same extension
    return unique_name





@router.post("/combineadhaar/{customer_id}",response_model=schemas.CustomerOut)
async def combine_adhaar(
    customer_id: int,
    db: Session = Depends(database.get_db),
    aadhaar_front_photo: UploadFile = File(...),
    aadhaar_back_photo: UploadFile = File(...),
):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

    aadhaar_front_io = BytesIO(aadhaar_front_photo.file.read())
    aadhaar_back_io = BytesIO(aadhaar_back_photo.file.read())
    combined_adhaar = utils.combine_images_vertically(aadhaar_front_io,aadhaar_back_io)
    combined_adhaar_io = BytesIO(combined_adhaar.read())
    compressed_adhaar = await utils.compress_image(combined_adhaar_io)
    aadhaar_filename = generate_unique_filename("aadhaarcombined.jpg")

    aadhaar_combined_url = await utils.upload_image_to_s3(compressed_adhaar, "tvstophaven", aadhaar_filename)

    customer.photo_adhaar_combined = aadhaar_combined_url

    db.commit()
    db.refresh(customer)
    return customer


BUCKET_NAME = "tvstophaven"


@router.post("/download-images/")
async def download_images(request: schemas.DownloadRequest):
    try:
        # Buffer for the ZIP file
        zip_buffer = io.BytesIO()

        # Initialize missing_files list
        missing_files = []

        # Create a ZipFile object in memory
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for image in request.image_urls:
                try:
                    # Cast the URL to a string explicitly
                    image_url = str(image.url)

                    # Fetch the image from the provided URL
                    response = requests.get(image_url)

                    # Check if the request was successful
                    if response.status_code == 200:
                        # Add the file to the ZIP
                        zip_file.writestr(image.name, response.content)
                    else:
                        logging.error(f"Failed to download {image.name} from {image_url}")
                        missing_files.append(image.name)
                except Exception as e:
                    logging.error(f"Error downloading image {image.name}: {e}")
                    missing_files.append(image.name)

        # Prepare the response
        zip_buffer.seek(0)  # Move pointer to the beginning for reading

        if missing_files:
            return JSONResponse(
                status_code=206,
                content={"message": "Download partially completed", "missing_files": missing_files}
            )

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=customer_{request.customer_id}_documents.zip"}
        )
    except Exception as e:
        logging.error(f"Error creating zip file: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ZIP file.")
