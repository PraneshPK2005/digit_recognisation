from keras.models import load_model
from collections import deque
import numpy as np
import cv2

# Load the models built in the previous steps
mlp_model = load_model("P:\dataset\sandy\Digits_Recognition\cnn_model.h5")
cnn_model = load_model("P:\dataset\sandy\Digits_Recognition\mlp_model.h5")

# Define the upper and lower boundaries for a color to be considered "Blue"
blueLower = np.array([100, 60, 60])
blueUpper = np.array([140, 255, 255])

# Define a 5x5 kernel for erosion and dilation
kernel = np.ones((5, 5), np.uint8)

# Define Black Board
blackboard = np.zeros((480, 640, 3), dtype=np.uint8)
digit = np.zeros((200, 200, 3), dtype=np.uint8)

# Setup deques to store digits drawn on screen
points = deque(maxlen=512)

# Define answer variables
ans1 = ' '
ans2 = ' '

index = 0
# Load the video
camera = cv2.VideoCapture(0)

# Keep looping
while True:
    # Grab the current paintWindow
    (grabbed, frame) = camera.read()
    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Determine which pixels fall within the blue boundaries and then blur the binary image
    blueMask = cv2.inRange(hsv, blueLower, blueUpper)
    blueMask = cv2.erode(blueMask, kernel, iterations=2)
    blueMask = cv2.morphologyEx(blueMask, cv2.MORPH_OPEN, kernel)
    blueMask = cv2.dilate(blueMask, kernel, iterations=1)

    # Find contours (bottle cap in my case) in the image
    cnts, _ = cv2.findContours(blueMask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = None

    # Check to see if any contours were found
    if len(cnts) > 0:
        # Sort the contours and find the largest one -- we
        # will assume this contour corresponds to the area of the bottle cap
        cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

        if len(cnt) >= 5:  # Ensure the contour has enough points
            # Get the radius of the enclosing circle around the found contour
            ((x, y), radius) = cv2.minEnclosingCircle(cnt)
            # Draw the circle around the contour
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            # Get the moments to calculate the center of the contour (in this case Circle)
            M = cv2.moments(cnt)
            if M['m00'] != 0:
                center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))
            else:
                center = None

            points.appendleft(center)

    elif len(cnts) == 0:
        if len(points) != 0:
            blackboard_gray = cv2.cvtColor(blackboard, cv2.COLOR_BGR2GRAY)
            blur1 = cv2.medianBlur(blackboard_gray, 15)
            blur1 = cv2.GaussianBlur(blur1, (5, 5), 0)
            thresh1 = cv2.threshold(blur1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            blackboard_cnts, _ = cv2.findContours(thresh1.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            if len(blackboard_cnts) >= 1:
                cnt = sorted(blackboard_cnts, key=cv2.contourArea, reverse=True)[0]

                if len(cnt) >= 5:  # Ensure contour has enough points
                    if cv2.contourArea(cnt) > 1000:
                        x, y, w, h = cv2.boundingRect(cnt)
                        digit = blackboard_gray[y-10:y + h + 10, x-10:x + w + 10]
                        newImage = cv2.resize(digit, (28, 28))
                        newImage = np.array(newImage)
                        newImage = newImage.astype('float32') / 255

                        ans1 = mlp_model.predict(newImage.reshape(1, 28, 28))[0]
                        ans1 = np.argmax(ans1)
                        ans2 = cnn_model.predict(newImage.reshape(1, 28, 28, 1))[0]
                        ans2 = np.argmax(ans2)

            # Empty the points deque and the blackboard
            points = deque(maxlen=512)
            blackboard = np.zeros((480, 640, 3), dtype=np.uint8)

    # Connect the points with a line
    for i in range(1, len(points)):
        if points[i - 1] is None or points[i] is None:
            continue
        cv2.line(frame, points[i - 1], points[i], (0, 0, 0), 2)
        cv2.line(blackboard, points[i - 1], points[i], (255, 255, 255), 8)

    # Put the result on the screen
    cv2.putText(frame, "Multilayer Perceptron: " + str(ans1), (10, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Convolution Neural Network: " + str(ans2), (10, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Show the frame
    cv2.imshow("Digits Recognition Real Time", frame)

    # If the 'q' key is pressed, stop the loop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
