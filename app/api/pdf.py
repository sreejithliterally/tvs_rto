from fastapi import APIRouter, Depends, HTTPException, FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List
from process_pdf import add_stamps_and_signature
import fitz  
from PIL import Image
import json
import os
import uuid

router = APIRouter(
    prefix="/pdf",
    tags=["Pdf editor"]
)

# Directories
STAMPS_DIR = "./stamps/"
SIGNATURES_DIR = "./uploads/signatures/"
OUTPUT_DIR = "./uploads/output/"
CHASSIS_IMAGE_DIR = "./uploads/chassis/"


# Ensure directories exist
os.makedirs(STAMPS_DIR, exist_ok=True)
os.makedirs(SIGNATURES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHASSIS_IMAGE_DIR, exist_ok=True)


with open("placement_config.json", "r") as config_file:
    placement_config = json.load(config_file)
with open("form21_config.json", "r") as config_file:
    form21_config = json.load(config_file)
with open("invoice_config.json","r") as config_file:
    invoice_config = json.load(config_file)
with open("disclaimer_config.json","r") as config_file:
    disclaimer_config = json.load(config_file)
with open("helmetcert_config.json","r") as config_file:
    helmetcert_config = json.load(config_file)
with open("inspection_config.json","r") as config_file:
    inspection_config = json.load(config_file)


@router.post("/process_pdf/invoice")
async def process_pdf(pdf: UploadFile = File(...), signature: UploadFile = File(...)):
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF.")
    if signature.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Signature must be an image (PNG or JPEG).")
    
    # Save uploaded files temporarily
    pdf_id = str(uuid.uuid4())
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_id}_{pdf.filename}")
    signature_path = os.path.join(SIGNATURES_DIR, f"{pdf_id}_{signature.filename}")
    finance_company = ''
    text_inputs = ''
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(await pdf.read())
    
    with open(signature_path, "wb") as sig_file:
        sig_file.write(await signature.read())
    
    # Process the PDF
    output_pdf_path = os.path.join(OUTPUT_DIR, f"processed_{pdf_id}_{pdf.filename}")
    try:
        add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, invoice_config, finance_company,text_inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        # Clean up temporary files
        os.remove(pdf_path)
        os.remove(signature_path)
    
    return FileResponse(output_pdf_path, filename=f"processed_{pdf.filename}", media_type='application/pdf')





@router.post("/process_pdf/form21")
async def process_pdf(pdf: UploadFile = File(...)):
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF.")
   
    # Save uploaded files temporarily
    pdf_id = str(uuid.uuid4())
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_id}_{pdf.filename}")
    
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(await pdf.read())
    

    signature_path=''
    finance_company = ''
    text_inputs = ''
    # Process the PDF
    output_pdf_path = os.path.join(OUTPUT_DIR, f"processed_{pdf_id}_{pdf.filename}")
    try:
        add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, form21_config, finance_company, text_inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        # Clean up temporary files
        os.remove(pdf_path)
     
    
    return FileResponse(output_pdf_path, filename=f"processed_{pdf.filename}", media_type='application/pdf')



@router.post("/process_pdf/form20")
async def process_pdf(pdf: UploadFile = File(...), signature: UploadFile = File(...),finance_company: str = Form(...)):
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF.")
    if signature.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Signature must be an image (PNG or JPEG).")
    
    # Save uploaded files temporarily
    pdf_id = str(uuid.uuid4())
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_id}_{pdf.filename}")
    signature_path = os.path.join(SIGNATURES_DIR, f"{pdf_id}_{signature.filename}")
    text_inputs = ''
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(await pdf.read())
    
    with open(signature_path, "wb") as sig_file:
        sig_file.write(await signature.read())
    
    # Process the PDF
    output_pdf_path = os.path.join(OUTPUT_DIR, f"processed_{pdf_id}_{pdf.filename}")
    try:
        add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, placement_config, finance_company,text_inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        # Clean up temporary files
        os.remove(pdf_path)
        os.remove(signature_path)
    
    return FileResponse(output_pdf_path, filename=f"processed_{pdf.filename}", media_type='application/pdf')




@router.post("/process_pdf/disclaimer")
async def process_pdf(pdf: UploadFile = File(...), signature: UploadFile = File(...)):
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF.")
    if signature.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Signature must be an image (PNG or JPEG).")
    
    # Save uploaded files temporarily
    pdf_id = str(uuid.uuid4())
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_id}_{pdf.filename}")
    signature_path = os.path.join(SIGNATURES_DIR, f"{pdf_id}_{signature.filename}")
    
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(await pdf.read())
    
    with open(signature_path, "wb") as sig_file:
        sig_file.write(await signature.read())
    finance_company =''
    text_inputs = ''
    # Process the PDF
    output_pdf_path = os.path.join(OUTPUT_DIR, f"processed_{pdf_id}_{pdf.filename}")
    try:
        add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, disclaimer_config, finance_company,text_inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        # Clean up temporary files
        os.remove(pdf_path)
        os.remove(signature_path)
    
    return FileResponse(output_pdf_path, filename=f"processed_{pdf.filename}", media_type='application/pdf')

@router.post("/process_pdf/helmetcert")
async def process_pdf_with_text(
    pdf: UploadFile = File(...), 
    customer_name: str = None, 
    chasis_number: str = None,
    signature: UploadFile = File(...),
    date: str = None 
):
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF.")
    if signature.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Signature must be an image (PNG or JPEG).")
    
    # Save uploaded files temporarily
    pdf_id = str(uuid.uuid4())
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_id}_{pdf.filename}")
    signature_path = os.path.join(SIGNATURES_DIR, f"{pdf_id}_{signature.filename}")
    
    try:    
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(await pdf.read())
        
        
        with open(signature_path, "wb") as sig_file:            
            sig_file.write(await signature.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving files: {e}")
    
    finance_company = ''  # You can modify this based on user input
    
    text_inputs = {
        "customer_name": customer_name,
        "chasis_number": chasis_number,
        "date": date,
        "dealer_name": "Top haven motors",
        "manufac": "TVS"
    }
    
    # Process the PDF
    output_pdf_path = os.path.join(OUTPUT_DIR, f"processed_{pdf_id}_{pdf.filename}")
    try:
        add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, helmetcert_config, finance_company, text_inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        # Clean up temporary files
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(signature_path):
            os.remove(signature_path)
    
    return FileResponse(output_pdf_path, filename=f"processed_{pdf.filename}", media_type='application/pdf')


@router.post("/process_pdf/inspection_letter")
async def process_pdf(
    pdf: UploadFile = File(...),
    sale_invoice_no: str = None, 
    chasis_number_pic: UploadFile = File(...),
    date: str = None):
    if pdf.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file is not a PDF.")
   
    # Save uploaded files temporarily
    pdf_id = str(uuid.uuid4())
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_id}_{pdf.filename}")
    chassis_image_path= os.path.join(CHASSIS_IMAGE_DIR, f"{pdf_id}_{chasis_number_pic.filename}")

    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(await pdf.read())
    with open(chassis_image_path, "wb") as chasis_file:
        chasis_file.write(await chasis_number_pic.read())
    

    signature_path=''
    finance_company = ''
    text_inputs = {
        "sale_invoice_no": sale_invoice_no,
        "date": date
    }
    
    # Process the PDF
    output_pdf_path = os.path.join(OUTPUT_DIR, f"processed_{pdf_id}_{pdf.filename}")
    try:
        add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, inspection_config, finance_company, text_inputs, chassis_image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    finally:
        # Clean up temporary files
        os.remove(pdf_path)
     
    
    return FileResponse(output_pdf_path, filename=f"processed_{pdf.filename}", media_type='application/pdf')

