from PIL import Image
import io
import hashlib

def upload(path):
    image = Image.open(path)
    image.load()
    if image.size != (1600, 1200):
        raise ValueError("Image must be 1600x1200 pixels")
    return image

def divide(image):
    blocks = []
    for j in range(0, 1200, 100):
        for i in range(0, 1600, 100):
            block = image.crop((i, j, i+100, j+100))
            buffer = io.BytesIO()
            block.save(buffer, format='JPEG')
            blocks.append((buffer.getvalue(), j // 100, i // 100))
    return blocks

def hash_blocks(blocks):
    hashes = []
    for block, row, col in blocks:
        data = row.to_bytes(2, "big") + col.to_bytes(2, "big") + block
        block_hash = hashlib.sha256(data).digest()
        hashes.append(block_hash)
    return hashes

if __name__ == "__main__":
    path = "test_images/test_1600x1200.jpg"
    image = upload(path)
    print(image.size)
    blocks = divide(image)
    print(len(blocks))
    print(len(blocks[0][0]))
    hashes = hash_blocks(blocks)
    print(len(hashes))
    print(len(hashes[0]))
    print(hashes[0].hex())
