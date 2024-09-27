import cv2
from django.http import StreamingHttpResponse, JsonResponse
from deepface import DeepFace
from django.shortcuts import render
import numpy as np
from collections import Counter

# Store emotions and stats for multiple faces
emotion_data = {
    "faces": [],  # Contains emotions for all detected faces
    "total_faces": 0,  # Number of faces in the current frame
    "emotion_percentages": {},  # Percentage breakdown of each emotion
    "most_frequent_emotion": "",  # Most common emotion across faces
    "emotion_timeline": []  # Stores the dominant emotion over time
}

MIN_FACE_SIZE = 100  # Minimum width/height for a face to be considered valid


# Real-time face and emotion detection using OpenCV and DeepFace
def face_emotion_detection(camera):
    global emotion_data
    emotion_counter = Counter()  # To count emotions in each frame

    while True:
        # Read frame from the camera
        success, frame = camera.read()
        if not success:
            break

        # Convert the frame to grayscale (for face detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load OpenCV's pre-trained face detection model
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        # Clear previous emotion data
        emotion_data["faces"] = []
        emotion_counter.clear()

        # If faces are detected, perform emotion analysis for each face
        for face_index, (x, y, w, h) in enumerate(faces, start=1):
            if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
                continue  # Skip faces that are too small
            # Crop the face region from the frame
            face_frame = frame[y : y + h, x : x + w]

            # Convert the face region from BGR (OpenCV format) to RGB (DeepFace format)
            rgb_face_frame = cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB)

            try:
                # DeepFace's emotion analysis for the face region
                emotion_analysis = DeepFace.analyze(
                    rgb_face_frame, actions=["emotion"], enforce_detection=False
                )
                emotions = (
                    emotion_analysis["emotion"]
                    if isinstance(emotion_analysis, dict)
                    else emotion_analysis[0]["emotion"]
                )
                dominant_emotion = (
                    emotion_analysis["dominant_emotion"]
                    if isinstance(emotion_analysis, dict)
                    else emotion_analysis[0]["dominant_emotion"]
                )

                # Convert emotions from NumPy types to native Python types
                emotions = {k: float(v) for k, v in emotions.items()}

                # Update emotion counter for stats
                emotion_counter[dominant_emotion] += 1
                emotion_data["emotion_timeline"].append(dominant_emotion)

                # Store the emotion data for each face
                emotion_data["faces"].append(
                    {
                        "x": int(x),
                        "y": int(y),
                        "w": int(w),
                        "h": int(h),
                        "emotions": emotions,
                        "dominant_emotion": dominant_emotion,
                    }
                )

                # Draw rectangles around the faces and display the dominant emotion
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Add the face index and dominant emotion
                label = f"Face {face_index}: {dominant_emotion}"
                cv2.putText(
                    frame,
                    label,
                    (x, y - 10),  # Position the text above the face rectangle
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (36, 255, 12),  # Green text color
                    2,
                )
            except Exception as e:
                print(f"Error detecting emotion for face: {e}")
                continue

        # Update overall stats for this frame
        total_faces = len(faces)
        emotion_data["total_faces"] = total_faces

        # Calculate emotion percentages
        if total_faces > 0:
            emotion_percentages = {
                emotion: (count / total_faces) * 100 for emotion, count in emotion_counter.items()
            }
        else:
            emotion_percentages = {}

        emotion_data["emotion_percentages"] = emotion_percentages

        # Find the most frequent emotion in this frame
        most_frequent_emotion = emotion_counter.most_common(1)
        if most_frequent_emotion:
            emotion_data["most_frequent_emotion"] = most_frequent_emotion[0][0]
        else:
            emotion_data["most_frequent_emotion"] = ""

        # Encode frame as JPEG
        ret, jpeg = cv2.imencode(".jpg", frame)
        frame = jpeg.tobytes()

        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")


# Streaming video feed with emotion detection
def video_feed(request):
    return StreamingHttpResponse(
        face_emotion_detection(cv2.VideoCapture(0)),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )


# Return emotion data for all faces as JSON
def get_emotion_data(request):
    return JsonResponse(emotion_data)


# Index view for rendering the template
def index(request):
    return render(request, "detection/index.html")
