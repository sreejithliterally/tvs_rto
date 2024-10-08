from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException,UploadFile,File, Form
from typing import List
from sqlalchemy.orm import Session
from uuid import uuid4
import models, schemas, database, oauth2
import utils
from PIL import Image
from datetime import datetime
from io import BytesIO

router = APIRouter(
    prefix="/chasis",
    tags=["Chasis number"]
    
)


@router.post("/upload", response_model=schemas.ChassisResponse)
async def upload_chassis_data(
    chassis_number: str = Form(...),
    chassis_photo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Validate the file type
    if chassis_photo.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG or PNG are allowed.")

    # Use chassis number as the filename for the photo
    file_extension = chassis_photo.filename.split('.')[-1]  # Get file extension (e.g., jpg, png)
    photo_filename = f"{chassis_number}.{file_extension}"  # Use chassis_number as the file name

    # Read the image data as a BytesIO object
    file_content = await chassis_photo.read()

    # Upload the file to S3 using chassis_number as the name
    s3_link = utils.upload_image_to_s3(BytesIO(file_content), "hogspot", photo_filename)

    # Save the chassis number, S3 link, and user who uploaded the file in the database
    new_chassis = models.Chassis(
        chassis_number=chassis_number,
        chassis_photo_url=s3_link,
        user_id=current_user.user_id
    )
    
    db.add(new_chassis)
    db.commit()     
    db.refresh(new_chassis)

    return new_chassis  


@router.get("image/{chassis_number}")
def get_chassis_image_link(
    chassis_number: str,
    db: Session = Depends(database.get_db)
):
    # Query the database for the chassis number
    chassis = db.query(models.Chassis).filter(models.Chassis.chassis_number == chassis_number).first()
    # If the chassis number is not found, raise an error
    if not chassis:
        raise HTTPException(status_code=404, detail="Chassis number not found")
    response_data = {
        "chassis_number": chassis.chassis_number,
        "image_url": chassis.chassis_photo_url,  # Assuming this exists in your Chassis model
    }

    # Return the response data
    return response_data
