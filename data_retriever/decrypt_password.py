from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv
from os import environ as env

load_dotenv()

class DecryptionException(Exception):
    def __init__(self, message):
        self.message = message

def decrypt(encrypted_base64: str) -> str:
    """
    Decrypt a base64 encoded encrypted password
    Args:
        encrypted_base64 (str): base64 encoded encrypted password
    Returns:
        str: decrypted password
    Raises:
        DecryptionException: If encrypted password cannot be decrypted
    """
    try:
        secret_key = env.get('ENCRYPTION_KEY')
        combined = b64decode(encrypted_base64)

        iv = combined[:16]
        auth_tag = combined[16:32]
        ciphertext = combined[32:]

        key = scrypt(secret_key, 'salt', 32, N=16384, r=8, p=1)

        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        cipher.update(b'')

        decrypted = cipher.decrypt_and_verify(ciphertext, auth_tag)
        return decrypted.decode('utf-8')
    except Exception as e:
        raise DecryptionException(e)

def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext password and return a base64-encoded string
    Returns:
        str: base64-encoded encrypted password
    """
    secret_key = env.get('ENCRYPTION_KEY')
    if not secret_key:
        raise ValueError("ENCRYPTION_KEY must be set in the environment.")

    key = scrypt(secret_key, 'salt', 32, N=16384, r=8, p=1)
    iv = get_random_bytes(16)

    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    cipher.update(b'')

    ciphertext, auth_tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    encrypted_data = iv + auth_tag + ciphertext
    return b64encode(encrypted_data).decode('utf-8')
