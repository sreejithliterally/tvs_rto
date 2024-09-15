from fastapi import status, HTTPException,Depends, APIRouter,UploadFile, File, Form
import boto3
from botocore.exceptions import NoCredentialsError
from config import settings
import uuid
import logging

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




AWS_SERVER_PUBLIC_KEY = settings.AWS_SERVER_PUBLIC_KEY
AWS_SERVER_SECRET_KEY = settings.AWS_SERVER_SECRET_KEY


def hash(password:str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)




def upload_image_to_s3(image, bucket_name):
    s3 = boto3.client('s3', aws_access_key_id=AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=AWS_SERVER_SECRET_KEY)
    try:
        unique_filename = f"{uuid.uuid4().hex}_{image.filename}"
        s3.upload_fileobj(image.file, bucket_name, unique_filename)
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_filename}"
        return image_url
    except NoCredentialsError:
        logging.error("Credentials not available")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 credentials not available")
    except Exception as e:
        logging.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error uploading image")
