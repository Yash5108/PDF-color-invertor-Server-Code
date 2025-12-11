import os
import io
import logging
from flask import Flask, request, send_file, render_template
import fitz # PyMuPDF
from PIL import Image, ImageOps

# --- Configuration ---
app = Flask(__name__)
# Define the path for the log file
LOG_FILE = os.path.join(os.path.dirname(__file__), 'inverter_log.txt')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# PDF Conversion Settings - Higher means better quality, but slower processing
PDF_ZOOM_FACTOR = 2 

# --- Core Processing Logic ---

def invert_pdf_colors_logic(input_pdf_bytes, filename):
    """
    Inverts colors of a PDF given its byte content. 
    Returns the inverted PDF content as a BytesIO object (in-memory).
    """
    logging.info(f"Processing started for file: {filename}")
    
    # Create an in-memory buffer to store the final output PDF
    output_buffer = io.BytesIO()
    
    try:
        # Open the PDF document from the bytes stream
        doc = fitz.open(stream=input_pdf_bytes, filetype="pdf")
        
        matrix = fitz.Matrix(PDF_ZOOM_FACTOR, PDF_ZOOM_FACTOR)
        processed_images = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convert raw pixel data (pix) to an in-memory stream for Pillow
            img_data = pix.tobytes("ppm") 
            img = Image.open(io.BytesIO(img_data))
            
            # 1. Invert Colors
            if img.mode != 'RGB':
                img = img.convert('RGB')
            inverted_img = ImageOps.invert(img)
            
            # 2. Store the processed image for later assembly
            processed_images.append(inverted_img.convert('RGB'))

        # Assemble into a new PDF and save to the in-memory buffer
        if processed_images:
            first_img = processed_images[0]
            other_images = processed_images[1:]

            first_img.save(
                output_buffer, 
                "PDF", 
                resolution=100.0, 
                save_all=True, 
                append_images=other_images
            )
            output_buffer.seek(0) # Rewind buffer to the beginning
            logging.info(f"Processing finished successfully for file: {filename}")
            return output_buffer 
        else:
            logging.error(f"Processing failed: No pages found in file: {filename}")
            return None

    except Exception as e:
        logging.error(f"Server Error processing file {filename}: {e}", exc_info=True)
        return None
    
# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    # Renders the HTML file from the 'templates' folder
    return render_template('index.html')

@app.route('/invert', methods=['POST'])
def invert_file():
    if 'pdf_file' not in request.files:
        return "No file part in the request.", 400
    
    file = request.files['pdf_file']
    filename = file.filename
    
    if filename == '':
        return "No file selected.", 400
        
    if file and filename.endswith('.pdf'):
        # Read the PDF content directly into memory
        pdf_bytes = file.read()
        
        # Process the PDF using the core logic
        inverted_pdf_buffer = invert_pdf_colors_logic(pdf_bytes, filename)
        
        if inverted_pdf_buffer:
            # Send the resulting file back to the user
            return send_file(
                inverted_pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"inverted_{filename}"
            )
        else:
            return "Error processing PDF.", 500
            
    return "Invalid file type. Please upload a PDF.", 400
