import cv2
import pickle
import cvzone
import numpy as np

def loadROI():
    with open(r"C:\Users\vijay\Downloads\NM-Project\Ai Enable Car Parking With OpenCV\Model building\parkingSlotPosition", 'rb') as f:
        posList = pickle.load(f)
    return posList

def checkParkingSpace(imgProcessed, img):
    spaceCounter = 0
    for pos in posList:
        x, y = pos
        imgCrop = imgProcessed[y:y + height, x:x + width]
        count = cv2.countNonZero(imgCrop)
        if count < 900:
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1
        else:
            color = (0, 0, 255)
            thickness = 2
        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20,
                       colorR=(0, 200, 0))

def processVideo():
    cap = cv2.VideoCapture(r"C:\Users\vijay\Downloads\NM-Project\Ai Enable Car Parking With OpenCV\Model building\carParkingInput.mp4")
    while True:
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        success, img = cap.read()
        if not success:
            break

        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        imgMedian = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

        checkParkingSpace(imgDilate, img)

        cv2.imshow("Image", img)
        if cv2.waitKey(10) == 27:  # If the 'Esc' key is pressed, exit the loop
            break

    # Release the video file and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    posList = loadROI()
    processVideo()
