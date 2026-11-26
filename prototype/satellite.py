from PIL import Image
import io
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes as crypto_hashes

HERE = Path(__file__).parent

WIDTH = 1600
HEIGHT = 1200
BLOCK = 100

def upload(path):
    image = Image.open(path)
    image.load()
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(f"Image must be {WIDTH}x{HEIGHT} pixels")
    return image

def divide(image):
    if WIDTH % BLOCK != 0 or HEIGHT % BLOCK != 0:
        raise ValueError(f"Image dimensions must be divisible by {BLOCK}")
    blocks = []
    for j in range(0, HEIGHT, BLOCK):
        for i in range(0, WIDTH, BLOCK):
            block = image.crop((i, j, i+BLOCK, j+BLOCK))
            buffer = io.BytesIO()
            block.save(buffer, format='JPEG')
            blocks.append((buffer.getvalue(), j // BLOCK, i // BLOCK))
    return blocks

def hash_blocks(blocks):
    hashes = []
    for block, row, col in blocks:
        data = row.to_bytes(2, "big") + col.to_bytes(2, "big") + block
        block_hash = hashlib.sha256(data).digest()
        hashes.append(block_hash)
    return hashes

def merkle_tree(hashes):
    hs = list(hashes)
    N = len(hashes)
    while N>1:
        isOdd = False
        if N % 2 == 1:
            N-= 1
            isOdd = True
        for i in range(0, N, 2):
            hs[i//2] = hashlib.sha256(hs[i] + hs[i+1]).digest()
        if isOdd:
            hs[N // 2] = hs[N]
            N = N // 2 + 1
        else:
            N = N // 2
    return hs[0]


def sign(root, private_key_path):
    with open(private_key_path, "rb") as f:
        serialized_private = f.read()
    private_key = serialization.load_pem_private_key(serialized_private, password=None)
    signature = private_key.sign(root, ec.ECDSA(crypto_hashes.SHA256()))

    return signature



if __name__ == "__main__":
    path = HERE / "test_images" / f"test_{WIDTH}x{HEIGHT}.jpg"
    image = upload(path)
    blocks = divide(image)
    hashes = hash_blocks(blocks)
    root = merkle_tree(hashes)
    signature = sign(root, HERE / "private_key.pem")

    print(f"Blocks: {len(blocks)}")
    print(f"Merkle root: {root.hex()}")
    print(f"Signature: {len(signature)} bytes")
