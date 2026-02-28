from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.padding import PKCS7
from base64 import b64encode, b64decode
import os, requests


def derive_key_and_iv(password, salt, iterations=1000):
    """Derives key and IV using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=48,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    key_iv = kdf.derive(password.encode())
    return key_iv[:32], key_iv[32:]  # Return key and iv separately


def encrypt(key_string, plaintext):
    salt = bytes([73, 118, 97, 110, 32, 77, 101, 100, 118, 101, 100, 101, 118])
    key, iv = derive_key_and_iv(key_string, salt)

    # print(f"Key : {', '.join(str(b) for b in key)}")
    # print(f"IV : {', '.join(str(b) for b in iv)}")

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Padding the plaintext to be a multiple of block size (16 bytes for AES)
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plaintext.encode("utf-16-le")) + padder.finalize()
    # padding_length = 16 - (len(plaintext.encode("utf-16-le")) % 16)
    # padded_plaintext = plaintext.encode("utf-16-le") + bytes(
    #     [padding_length] * padding_length
    # )

    encrypted_bytes = encryptor.update(padded_plaintext) + encryptor.finalize()
    return b64encode(encrypted_bytes).decode()


def decrypt(key_string, encrypted_data):
    salt = bytes([73, 118, 97, 110, 32, 77, 101, 100, 118, 101, 100, 101, 118])
    key, iv = derive_key_and_iv(key_string, salt)

    encrypted_bytes = b64decode(encrypted_data)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_padded_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

    # Remove padding
    padding_length = decrypted_padded_bytes[-1]
    decrypted_bytes = decrypted_padded_bytes[:-padding_length]

    return decrypted_bytes.decode("utf-16-le")
