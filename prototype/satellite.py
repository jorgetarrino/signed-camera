from PIL import Image

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
            blocks.append((block, j // 100, i // 100))
    return blocks


if __name__ == "__main__":
    path = "test_images/test_1600x1200.jpg"
    image = upload(path)
    print(image.size)
    blocks = divide(image)
    print(blocks[0][1:], blocks[-1][1:])
