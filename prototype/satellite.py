from PIL import Image

def upload(path):
    image = Image.open(path)
    image.load()
    if image.size != (1600, 1200):
        raise ValueError("Image must be 1600x1200 pixels")
    return image

if __name__ == "__main__":
    path = "test_images/test_1600x1200.jpg"
    image = upload(path)
    print(image.size)
