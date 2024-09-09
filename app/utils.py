import boto3
from botocore.exceptions import NoCredentialsError

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password:str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)




bucket_name = "travelactivity"

def upload_image_to_s3(image, bucket_name):
    s3 = boto3.client('s3')
    try:
        s3.upload_fileobj(image.file, bucket_name, image.filename)
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{image.filename}"
        return image_url
    except NoCredentialsError:
        return None