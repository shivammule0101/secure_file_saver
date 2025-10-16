from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
from encrypt_util import generate_key, encrypt_file, decrypt_file
import os

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'change_this_to_a_random_secret_in_production'

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        flash('No file provided')
        return redirect(url_for('index'))
    filename = secure_filename(f.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(save_path)
    # Generate key and encrypt
    key = generate_key()
    encrypted_path = save_path + '.enc'
    encrypt_file(save_path, encrypted_path, key)
    # remove original (simulate encrypt-before-cloud-upload)
    os.remove(save_path)
    # show key to user to store safely
    return render_template('upload_success.html', filename=os.path.basename(encrypted_path), key=key.decode())

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/decrypt', methods=['GET','POST'])
def decrypt():
    if request.method == 'GET':
        files = [fn for fn in os.listdir(app.config['UPLOAD_FOLDER']) if fn.endswith('.enc')]
        return render_template('decrypt.html', files=files)
    # POST - perform decryption and stream the decrypted file
    enc_filename = request.form.get('filename')
    key = request.form.get('key')
    if not enc_filename or not key:
        flash('Provide both filename and key')
        return redirect(url_for('decrypt'))
    enc_path = os.path.join(app.config['UPLOAD_FOLDER'], enc_filename)
    if not os.path.exists(enc_path):
        flash('Encrypted file not found')
        return redirect(url_for('decrypt'))
    try:
        decrypted_bytes = decrypt_file(enc_path, key.encode())
    except Exception as e:
        flash('Decryption failed: ' + str(e))
        return redirect(url_for('decrypt'))
    # stream decrypted data as attachment
    original_name = enc_filename[:-4]  # remove .enc
    return Response(decrypted_bytes, headers={
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{original_name}"'
    })

if __name__ == '__main__':
    # For demo use only. In production, use a proper WSGI server.
    app.run(host='0.0.0.0', port=5000, debug=True)
