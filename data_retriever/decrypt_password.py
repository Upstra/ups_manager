from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from os import environ as env


def decrypt(encrypted_base64: str) -> str:
    """
    Decrypt a base64 encoded encrypted password
    Args:
        encrypted_base64 (str): base64 encoded encrypted password
    Returns:
        str: decrypted password
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
        print(f"Decryption failed: {e}")
        raise
