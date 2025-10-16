from cryptography.fernet import Fernet

def generate_key():
    """Return a new Fernet key as bytes."""
    return Fernet.generate_key()

def encrypt_file(in_path: str, out_path: str, key: bytes):
    """Read in_path bytes, encrypt with key, write to out_path."""
    f = Fernet(key)
    with open(in_path, 'rb') as fin:
        data = fin.read()
    token = f.encrypt(data)
    with open(out_path, 'wb') as fout:
        fout.write(token)

def decrypt_file(enc_path: str, key: bytes) -> bytes:
    """Return decrypted bytes from enc_path using key."""
    f = Fernet(key)
    with open(enc_path, 'rb') as fin:
        token = fin.read()
    return f.decrypt(token)
