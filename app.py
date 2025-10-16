from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, Response, jsonify, abort
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
    # Home page: file explorer
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('home.html', files=files)


@app.route('/add', methods=['GET'])
def add_view():
    # upload page
    return render_template('add.html')

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'no file provided'}), 400
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
    # return JSON for AJAX uploads, otherwise render success page
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'id': os.path.basename(encrypted_path), 'name': os.path.basename(encrypted_path), 'key': key.decode()})
    # render upload/add page and show the key so user can store it
    return render_template('add.html', filename=os.path.basename(encrypted_path), key=key.decode())

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/serve/<path:filename>')
def serve_alias(filename):
    # backward-compatible alias used by client JS
    return serve_file(filename)


@app.route('/api/files')
def api_files():
    files = [fn for fn in os.listdir(app.config['UPLOAD_FOLDER'])]
    # simple metadata: id == filename
    items = [{'id': fn, 'name': fn} for fn in files]
    return jsonify(items)


@app.route('/api/files/<path:file_id>')
def api_file_meta(file_id):
    path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(path):
        return jsonify({'error': 'not found'}), 404
    return jsonify({'id': file_id, 'name': file_id, 'encrypted_url': url_for('serve_file', filename=file_id)})


@app.route('/file/<path:file_id>')
def file_view(file_id):
    # render a dedicated file view page
    if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], file_id)):
        abort(404)
    return render_template('file.html', file_id=file_id)


@app.route('/file/<path:file_id>/download', methods=['POST'])
def file_download_decrypted(file_id):
    # accept JSON {key}
    data = request.get_json() or {}
    key = data.get('key')
    if not key:
        return 'Missing key', 400
    enc_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(enc_path):
        return 'Encrypted file not found', 404
    try:
        decrypted_bytes = decrypt_file(enc_path, key.encode())
    except Exception as e:
        return f'Decryption failed: {e}', 400
    original_name = file_id[:-4] if file_id.endswith('.enc') else file_id
    return Response(decrypted_bytes, headers={
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{original_name}"'
    })

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
