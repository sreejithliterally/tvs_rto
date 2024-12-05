import fitz  
import os

STAMPS_DIR = "./stamps/"
SIGNATURES_DIR = "./uploads/signatures/"
CHASSIS_IMAGE_DIR = "./uploads/chassis/"




os.makedirs(STAMPS_DIR, exist_ok=True)
os.makedirs(SIGNATURES_DIR, exist_ok=True)
os.makedirs(CHASSIS_IMAGE_DIR, exist_ok=True)

MIN_SIZE_POINTS = 0.20 * 72

def add_stamps_and_signature(pdf_path, signature_path, output_pdf_path, config, selected_finance, text_inputs,chassis_image_path=None):
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
            text_to_add = text_inputs.get(text_item["key"], "")  # Get user input for this key
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
    
    large_box_count = 0  # Initialize a counter for boxes larger than 0.29 inches

    # Iterate through each page in the document
    for page_num in range(len(doc)):
        page = doc[page_num]  # Get the current page
        
        # Get all graphical elements (drawings) on the page
        drawings = page.get_drawings()
        
        # Count and place image in rectangles larger than 0.29 inches
        for drawing in drawings:
            # Check if the drawing has a 'rect' attribute
            if 'rect' in drawing:
                rect = drawing['rect']
                # Check if the rectangle dimensions are greater than 0.29 inches
                if rect.width > MIN_SIZE_POINTS and rect.height > MIN_SIZE_POINTS:
                    large_box_count += 1  # Increment the count

                    # Calculate the center position for the image
                    image_width, image_height = 20, 20  # Adjust these based on the desired image size in points
                    center_x = rect.x0 + (rect.width - image_width) / 2
                    center_y = rect.y0 + (rect.height - image_height) / 2
                    image_rect = fitz.Rect(center_x, center_y, center_x + image_width, center_y + image_height)

                    # Insert the image in the center òf the box
                    page.insert_image(image_rect, filename=image_path)



    if chassis_image_path and os.path.exists(chassis_image_path):
        chassis_config = config.get("chassis_image")
        if chassis_config:
            for placement in chassis_config["placements"]:
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
                page.insert_image(rect, filename=chassis_image_path)
    
    
    # Save the modified PDF
    # doc.save(output_pdf_path)
    doc.close()

image_path = "./assets/ticknew.png"
