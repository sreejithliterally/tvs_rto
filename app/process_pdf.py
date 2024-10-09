import fitz  
import os

STAMPS_DIR = "./stamps/"
SIGNATURES_DIR = "./uploads/signatures/"


os.makedirs(STAMPS_DIR, exist_ok=True)
os.makedirs(SIGNATURES_DIR, exist_ok=True)



def add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, config, selected_finance, text_inputs):
    # Open the PDF
    doc = fitz.open(pdf_path)

    # Add stamps
    for stamp in config.get("stamps", []):
        stamp_image_path = os.path.join(STAMPS_DIR, stamp["name"])
        if not os.path.exists(stamp_image_path):
            raise FileNotFoundError(f"Stamp image '{stamp['name']}' not found in stamps directory.")
        
        for placement in stamp["placements"]:
            page_number = placement["page"]
            if page_number - 1 < 0 or page_number - 1 >= len(doc):
                raise IndexError(f"Page number {page_number} is out of range for the PDF.")
            
            page = doc[page_number - 1]
            rect = fitz.Rect(
                placement["position"]["x"],
                placement["position"]["y"],
                placement["position"]["x"] + placement["width"],
                placement["position"]["y"] + placement["height"]
            )
            page.insert_image(rect, filename=stamp_image_path)
    
    # Add finance seals
    finance_config = config.get("finances", {}).get(selected_finance)
    if finance_config:
        for seal in finance_config.get("seals", []):
            finance_image_path = os.path.join(STAMPS_DIR, seal["name"])
            if not os.path.exists(finance_image_path):
                raise FileNotFoundError(f"Finance image '{seal['name']}' not found in stamps directory.")
            
            for placement in seal["placements"]:
                page_number = placement["page"]
                if page_number - 1 < 0 or page_number - 1 >= len(doc):
                    raise IndexError(f"Page number {page_number} is out of range for the PDF.")
                
                page = doc[page_number - 1]
                rect = fitz.Rect(
                    placement["position"]["x"],
                    placement["position"]["y"],
                    placement["position"]["x"] + placement["width"],
                    placement["position"]["y"] + placement["height"]
                )
                page.insert_image(rect, filename=finance_image_path)

    # Add signature
    signature_config = config.get("signature")
    if signature_config:
        for placement in signature_config["placements"]:
            page_number = placement["page"]
            if page_number - 1 < 0 or page_number - 1 >= len(doc):
                raise IndexError(f"Page number {page_number} is out of range for the PDF.")
            
            page = doc[page_number - 1]
            rect = fitz.Rect(
                placement["position"]["x"],
                placement["position"]["y"],
                placement["position"]["x"] + placement["width"],
                placement["position"]["y"] + placement["height"]
            )
            page.insert_image(rect, filename=signature_path)

    for text_item in config.get("texts", []):
        page_number = text_item["page"]
        if page_number - 1 < 0 or page_number - 1 >= len(doc):
            raise IndexError(f"Page number {page_number} is out of range for the PDF.")
        
        page = doc[page_number - 1]
        if "key" in text_item:  # Dynamic text
            text_to_add = text_inputs.get(text_item["key"], "Default Text")  # Get user input for this key
        elif "text" in text_item:  # Static text
            text_to_add = text_item["text"]  # Use predefined static text

        position = text_item["position"]
        font_size = text_item.get("font_size", 12)
        text_color = text_item.get("color", (0, 0, 0))
        
        # Draw the text on the page at the specified position
        page.insert_text(
            (position["x"], position["y"]),
            text_to_add,
            fontsize=font_size,
            color=text_color
        )
    
    # Save the modified PDF
    doc.save(output_pdf_path)
    doc.close()

    
