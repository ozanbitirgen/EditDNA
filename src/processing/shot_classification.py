"""
Shot classification module for video analysis.
"""
import cv2
import numpy as np
from typing import List
from ..models.data_models import Shot

def classify_shots(video_path: str, shots: List[Shot]) -> List[Shot]:
    """
    Classify each shot by analyzing key frames.
    
    Args:
        video_path: Path to the video file
        shots: List of Shot objects to classify
        
    Returns:
        Updated list of Shot objects with classification
    """
    print(f"[INFO] Classifying {len(shots)} shots ...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        return shots

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    for shot in shots:
        # Sample a frame at the middle of the shot
        t_mid = (shot.t_start + shot.t_end) / 2.0
        frame_idx = int(t_mid * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret or frame is None:
            shot.shot_type = "UNKNOWN"
            shot.faces_present = 0
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        num_faces = len(faces)
        shot.faces_present = num_faces
        shot.shot_type = "TALKING_HEAD" if num_faces > 0 else "BROLL"

    cap.release()
    return shots