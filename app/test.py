
import cv2
from PIL import Image

img = cv2.imread('./custtr.jpeg', cv2.IMREAD_GRAYSCALE)

# define a threshold
thresh = 110

# threshold the image
img = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY)[1]

#convert nparray data
img = Image.fromarray(img)
img = img.convert("RGBA")

pixdata = img.load()

width, height = img.size
for y in range(height):
    for x in range(width):
        if pixdata[x, y] == (255, 255, 255, 255):   #transparent
            pixdata[x, y] = (255, 255, 255, 0)

img.save("img2.png", "PNG")