import os
import fitz
from PIL import Image, ImageOps
import io
from flask import Flask, request, send_file, render_template

# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads' # Temporary folder for uploaded files

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Your core PDF processing logic, modified to take file content
def invert_pdf_colors_logic(input_pdf_bytes):
    """
    Inverts colors of a PDF given its byte content and returns the inverted PDF as bytes.
    """
    # Create an in-memory buffer to store the final output PDF
    output_buffer = io.BytesIO()
    temp_image_paths = []
    
    try:
        # Open the PDF document from the bytes
        doc = fitz.open(stream=input_pdf_bytes, filetype="pdf")
        zoom_factor = 2 
        matrix = fitz.Matrix(zoom_factor, zoom_factor)
        
        processed_images = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convert raw pixel data to an in-memory stream for Pillow
            img_data = pix.tobytes("ppm") 
            img = Image.open(io.BytesIO(img_data))
            
            # Invert Colors
            if img.mode != 'RGB':
                img = img.convert('RGB')
            inverted_img = ImageOps.invert(img)
            
            # Append the processed image (converted to RGB for PDF saving)
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
            return output_buffer # Return the BytesIO object
        else:
            return None

    except Exception as e:
        print(f"Server Error during processing: {e}")
        return None
    
# Flask route to handle the main page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Flask route to handle the file upload and processing
@app.route('/invert', methods=['POST'])
def invert_file():
    # Check if a file was uploaded
    if 'pdf_file' not in request.files:
        return "No file part in the request.", 400
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        return "No file selected.", 400
        
    if file and file.filename.endswith('.pdf'):
        # Read the PDF content directly into memory
        pdf_bytes = file.read()
        
        # Process the PDF using the core logic
        inverted_pdf_buffer = invert_pdf_colors_logic(pdf_bytes)
        
        if inverted_pdf_buffer:
            # Send the resulting file back to the user
            return send_file(
                inverted_pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"inverted_{file.filename}"
            )
        else:
            return "Error processing PDF.", 500
            
    return "Invalid file type. Please upload a PDF.", 400

if __name__ == '__main__':
    # You will use a production server like Gunicorn/Waitress for actual deployment
    app.run(debug=True)
