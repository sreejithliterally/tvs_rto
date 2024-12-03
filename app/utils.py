from io import BytesIO
from fastapi import status, HTTPException,Depends, APIRouter,UploadFile, File, Form
import boto3
from botocore.exceptions import NoCredentialsError
from config import settings
import uuid
import logging
import cv2
import numpy as np
from PIL import Image
import os
from passlib.context import CryptContext
from fastapi.responses import StreamingResponse


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




AWS_SERVER_PUBLIC_KEY = settings.AWS_SERVER_PUBLIC_KEY
AWS_SERVER_SECRET_KEY = settings.AWS_SERVER_SECRET_KEY


def hash(password:str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)




async def upload_image_to_s3(image: BytesIO, bucket_name: str, file_name: str = None) -> str:
    s3 = boto3.client('s3', aws_access_key_id=AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=AWS_SERVER_SECRET_KEY)
    try:
        # Generate unique filename if not provided
        unique_filename = file_name if file_name else f"{uuid.uuid4().hex}.jpg"

        # Upload the file to the S3 bucket
        s3.upload_fileobj(image, bucket_name, unique_filename)

        # Construct the public URL for the uploaded image
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{unique_filename}"
        return image_url

    except NoCredentialsError:
        logging.error("S3 credentials not available")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="S3 credentials not available")
    
    except Exception as e:
        logging.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error uploading image")


def get_s3_client():
    try:
        return boto3.client(
            's3',
            aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
            aws_secret_access_key=AWS_SERVER_SECRET_KEY
        )
    except NoCredentialsError:
        logging.error("S3 credentials not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 credentials not available"
        )


def edge_detect_and_crop(uploaded_file):
    contents = uploaded_file.file.read()
    npimg = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError("Could not decode the image.")

    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image = cv2.resize(image, (500, int(image.shape[1] * ratio)))

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # Debugging: Show the edged image (optional, remove in production)
    cv2.imshow("Edges", edged)
    cv2.waitKey(0)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            break

    if screenCnt is None:
        raise ValueError("No document found")

    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
    
    # Convert the cropped image back to a format suitable for return
    img = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    file_object = io.BytesIO()
    img = Image.fromarray(img)
    img.save(file_object, 'PNG')
    file_object.seek(0)

    return file_object

def four_point_transform(image, pts):
    rect = order_points(pts)  # Order points in a consistent manner
    (tl, tr, br, bl) = rect  # Unpack ordered points

    # Compute the width of the new image
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    # Compute the height of the new image
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    # Set destination points for the perspective transformation
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Compute the perspective transformation matrix
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped  # Return the transformed image


def order_points(pts):
    # Initialize a list of coordinates
    rect = np.zeros((4, 2), dtype="float32")

    # Sum the coordinates to get top-left and bottom-right
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-left
    rect[2] = pts[np.argmax(s)]  # Bottom-right

    # Compute the difference to get top-right and bottom-left
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right
    rect[3] = pts[np.argmax(diff)]  # Bottom-left

    return rect




def combine_images_vertically(cropped_image1: BytesIO, cropped_image2: BytesIO) -> BytesIO:
    # Load the cropped images from BytesIO
    image1 = Image.open(cropped_image1)
    image2 = Image.open(cropped_image2)
    
    # Get the width and height of both images
    width1, height1 = image1.size
    width2, height2 = image2.size

    # Create a new image with the width of the wider image and the combined height
    total_height = height1 + height2
    max_width = max(width1, width2)
    
    # Create a blank image for the combined result
    combined_image = Image.new("RGB", (max_width, total_height))
    
    # Paste the first image at the top and the second image below it
    combined_image.paste(image1, (0, 0))
    combined_image.paste(image2, (0, height1))
    
    # Save combined image to BytesIO
    combined_image_bytes = BytesIO()
    combined_image.save(combined_image_bytes, format='JPEG')
    combined_image_bytes.seek(0)
    
    return combined_image_bytes



async def compress_image(file, min_size_kb=300, max_size_kb=400) -> BytesIO:
    # Check if input is `UploadFile`; if so, read it into `bytes`
    if isinstance(file, UploadFile):
        file_bytes = await file.read()  # Use await if it's an UploadFile
        file_stream = BytesIO(file_bytes)
    elif isinstance(file, BytesIO):
        file_stream = file  # Already a BytesIO object
    else:
        raise TypeError("Unsupported file type. Must be UploadFile or BytesIO.")

    # Open the image using PIL
    image = Image.open(file_stream)

    # Convert to RGB if necessary
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    quality = 85
    compressed_image = BytesIO()

    while True:
        compressed_image.seek(0)
        compressed_image.truncate(0)
        
        image.save(compressed_image, format='JPEG', quality=quality)
        size_kb = compressed_image.tell() / 1024
        
        # Check size constraints
        if min_size_kb <= size_kb <= max_size_kb:
            break
        elif size_kb < min_size_kb:
            quality += 5
        else:
            quality -= 5

        if quality < 10 or quality > 95:
            break

    compressed_image.seek(0)
    return compressed_image