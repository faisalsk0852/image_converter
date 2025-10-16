import os
import uuid
import shutil
import io
import zipfile
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

app = Flask(__name__)
TEMP_FOLDER = 'temp_uploads'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = request.files.getlist('images')
    if not uploaded_files or uploaded_files[0].filename == '':
        return "No files selected. Please go back and choose your images."
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(TEMP_FOLDER, session_id)
    images_dir = os.path.join(temp_dir, 'images')
    os.makedirs(images_dir)
    memory_file = io.BytesIO()
    try:
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for image_file in uploaded_files:
                try:
                    base_name = os.path.splitext(image_file.filename)[0]
                    final_image_name = secure_filename(base_name) + ".jpg"
                    final_html_name = secure_filename(base_name) + ".html"
                    save_path = os.path.join(images_dir, final_image_name)
                    image = Image.open(image_file.stream)
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(save_path, 'jpeg')
                    html_content = f"""<!DOCTYPE html>
<html>
<head>
<title>{base_name}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    body {{ margin: 0; padding: 0 32px; box-sizing: border-box; background-color: #FFFFFF; }}
    img {{ width: 100%; display: block; }}
</style>
</head>
<body>
<img src="images/{final_image_name}" alt="">
</body>
</html>"""
                    zf.write(save_path, arcname=os.path.join('images', final_image_name))
                    zf.writestr(final_html_name, html_content)
                except UnidentifiedImageError:
                    print(f"Skipping non-image file: {image_file.filename}")
                    continue
    finally:
        shutil.rmtree(temp_dir)
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='generated_html_files.zip'
    )

@app.route('/link-creator', methods=['GET', 'POST'])
def link_creator():
    final_links = None
    if request.method == 'POST':
        # Get the entire block of text from the textarea
        user_links_input = request.form.get('ftp_links', '')
        # Split the text into a list of individual links, one per line
        raw_links = user_links_input.strip().splitlines()
        
        final_links = []
        prefix_to_remove = "ftp://u111969758@153.92.8.191/domains/skydevstaging.com/public_html"
        base_url_to_add = "https://skydevstaging.com"
        
        # Loop through each link from the list
        for link in raw_links:
            link = link.strip() # Remove any leading/trailing whitespace
            if not link:
                continue # Skip empty lines

            if link.startswith(prefix_to_remove):
                remaining_part = link.replace(prefix_to_remove, "", 1)
                new_link = base_url_to_add + remaining_part
                final_links.append(new_link)
            else:
                # Add an error message for any line that doesn't match
                final_links.append(f"ERROR: Invalid prefix for -> {link}")

    return render_template('link_converter.html', final_links=final_links)

if __name__ == '__main__':
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    app.run(debug=True)