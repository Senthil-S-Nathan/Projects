import cv2
import pickle

width, height = 107, 48

try:
    with open(r"C:\Users\vijay\Downloads\NM-Project\Ai Enable Car Parking With OpenCV\Model building\parkingSlotPosition", "rb") as f:
        posList = pickle.load(f)
except FileNotFoundError:
    posList = []

def mouseClick(event, x, y, flags, params):
    global posList
    if event == cv2.EVENT_LBUTTONDOWN:
        posList.append((x, y))
    elif event == cv2.EVENT_RBUTTONDOWN:
        for i, pos in enumerate(posList):
            x1, y1 = pos
            if x1 <= x <= x1 + width and y1 <= y <= y1 + height:
                posList.pop(i)
    elif event == cv2.EVENT_LBUTTONUP or event == cv2.EVENT_RBUTTONUP:
        with open(r"C:\Users\vijay\Downloads\NM-Project\Ai Enable Car Parking With OpenCV\Model building\parkingSlotPosition", "wb") as f:
            pickle.dump(posList, f)

img = cv2.imread(r"C:\Users\vijay\Downloads\NM-Project\Ai Enable Car Parking With OpenCV\Model building\carParkImg.png")

cv2.namedWindow("Image")
cv2.setMouseCallback("Image", mouseClick)

while True:
    for pos in posList:
        x, y = pos
        cv2.rectangle(img, (x, y), (x + width, y + height), (255, 255, 255), 2)

    cv2.imshow("Image", img)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break

cv2.destroyAllWindows()
