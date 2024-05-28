import os
import qrcode
import vobject
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from base64 import b64encode

# Absolute path to the index.html file
index_file_path = 'C:/Users/sulta/Downloads/texttoqr (1)/texttoqr/index.html'

# Directory to store HTML files, QR codes, and vCards
output_dir = 'C:/Users/sulta/Downloads/texttoqr (1)/texttoqr/output'
os.makedirs(output_dir, exist_ok=True)

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in [' ', '.', '_', '-'] else '_' for c in name).replace(' ', '_')

def create_vcard(contact):
    vcard = vobject.vCard()
    vcard.add('n').value = vobject.vcard.Name(family=contact['name_ar'], given=contact['name_en'])
    vcard.add('fn').value = contact['name_en']
    vcard.add('org').value = [contact['department'], contact['directorate']]
    vcard.add('title').value = contact['position']
    vcard.add('tel').value = contact['phone']
    vcard.add('email').value = contact['email']
    vcard.add('url').value = contact['website']
    vcard.add('adr').value = vobject.vcard.Address(street=contact['address'])
    
    return vcard.serialize()

def save_vcard(vcard_data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(vcard_data)
    print(f"vCard saved: {file_path}")

def generate_qr_code(data, output_file):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_file)
    print(f"QR code generated: {output_file}")

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return b64encode(image_file.read()).decode('utf-8')

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/generate':
            params = parse_qs(parsed_path.query)
            contact = {
                'name_ar': params.get('arname', [''])[0],
                'name_en': params.get('enname', [''])[0],
                'position': params.get('position', [''])[0],
                'department': params.get('department', [''])[0],
                'directorate': params.get('directorate', [''])[0],
                'phone': params.get('phone', [''])[0],
                'email': params.get('email', [''])[0],
                'website': params.get('website', [''])[0],
                'address': params.get('address', [''])[0]
            }
            sanitized_name = sanitize_filename(contact['name_en'])
            qr_code_file = os.path.join(output_dir, f"{sanitized_name}_qrcode.png")
            vcard_file = os.path.join(output_dir, f"{sanitized_name}_contact.vcf")
            
            vcard_data = create_vcard(contact)
            save_vcard(vcard_data, vcard_file)
            generate_qr_code(vcard_data, qr_code_file)

            qr_code_base64 = get_base64_image(qr_code_file)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Generated Contact Information</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: auto;
                            padding: 20px;
                            border: 1px solid #ccc;
                            border-radius: 10px;
                            box-shadow: 0 0 10px rgba(0,0,0,0.1);
                            text-align: center;
                        }}
                        .qr-code {{
                            margin: 20px 0;
                            width: 100%;
                            height: auto;
                        }}
                        .title {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="title">{contact['name_ar']}</h1>
                        <p><strong>Name:</strong> {contact['name_en']}</p>
                        <p><strong>Position:</strong> {contact['position']}</p>
                        <p><strong>Department:</strong> {contact['department']}</p>
                        <p><strong>Directorate:</strong> {contact['directorate']}</p>
                        <p><strong>Phone:</strong> {contact['phone']}</p>
                        <p><strong>Email:</strong> <a href="mailto:{contact['email']}">{contact['email']}</a></p>
                        <p><strong>Website:</strong> <a href="{contact['website']}" target="_blank">{contact['website']}</a></p>
                        <p><strong>Address:</strong> {contact['address']}</p>
                        <div class="qr-code">
                            <img src="data:image/png;base64,{qr_code_base64}" alt="QR Code">
                        </div>
                        <p><a href="/output/{sanitized_name}_contact.vcf" download>Download vCard</a></p>
                    </div>
                </body>
                </html>
            """.encode('utf-8'))
        elif parsed_path.path == '/':
            self.path = index_file_path
            with open(index_file_path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        else:
            # Serve files from the output directory
            requested_path = parsed_path.path.lstrip('/')
            full_path = os.path.join(output_dir, requested_path)
            print(f"Serving file: {full_path}")
            if os.path.exists(full_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                with open(full_path, 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404, "File not found")

PORT = 12007
IP = '0.0.0.0'  # Bind to all available interfaces, including localhost

with HTTPServer((IP, PORT), CustomHTTPRequestHandler) as httpd:
    print(f"Serving at {IP} port {PORT}")
    httpd.serve_forever()
