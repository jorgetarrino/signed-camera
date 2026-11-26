from PIL import Image
import io
import hashlib
from pathlib import Path

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


if __name__ == "__main__":
    path = HERE / "test_images" / f"test_{WIDTH}x{HEIGHT}.jpg"
    image = upload(path)
    print(image.size)
    blocks = divide(image)
    print(len(blocks))
    print(len(blocks[0][0]))
    hashes = hash_blocks(blocks)
    print(len(hashes))
    print(len(hashes[0]))
    print(hashes[0].hex())
    
    # Prueba 1: caso pequeño con 3 hashes (nivel impar)
    a, b, c = b"A", b"B", b"C"
    root_test = merkle_tree([a, b, c])
    expected = hashlib.sha256(hashlib.sha256(a + b).digest() + c).digest()
    print("3 hashes:", root_test == expected)

    # Prueba 2: los 192 hashes reales de la imagen
    root = merkle_tree(hashes)
    print("Raíz:", root.hex())
    print("¿Hashes intactos?:", len(hashes) == 192)
