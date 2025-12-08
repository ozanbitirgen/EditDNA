"""
OCR processing module for text extraction from video frames.
"""
import cv2
import pytesseract
from typing import List, Dict, Any
from ..models.data_models import Shot

def estimate_text_position(frame_shape, bbox) -> str:
    """Estimate text position in frame (TOP/BOTTOM/CENTER)."""
    _, h = frame_shape[1], frame_shape[0]
    x, y, w, h_box = bbox
    center_y = y + h_box / 2
    rel = center_y / h
    return "TOP" if rel < 0.33 else "BOTTOM" if rel > 0.66 else "CENTER"

def extract_ocr(video_path: str, shots: List[Shot]) -> List[Shot]:
    """
    Extract text from video frames using OCR.
    
    Args:
        video_path: Path to the video file
        shots: List of Shot objects to process
        
    Returns:
        Updated list of Shot objects with OCR results
    """
    print(f"[INFO] Extracting OCR for {len(shots)} shots ...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video for OCR: {video_path}")
        return shots

    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    for shot in shots:
        t_mid = (shot.t_start + shot.t_end) / 2.0
        frame_idx = int(t_mid * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret or frame is None:
            shot.overlay_texts = []
            continue

        data = pytesseract.image_to_data(frame, output_type=pytesseract.Output.DICT)
        overlay_texts = []

        for i in range(len(data['level'])):
            text = data['text'][i].strip()
            if not text:
                continue
                
            (x, y, w, h) = (data['left'][i], data['top'][i],
                            data['width'][i], data['height'][i])
            pos = estimate_text_position(frame.shape, (x, y, w, h))

            overlay_texts.append({
                "text": text,
                "bbox": {"x": x, "y": y, "w": w, "h": h},
                "position": pos,
                "is_caption": (pos == "BOTTOM")
            })

        shot.overlay_texts = overlay_texts

    cap.release()
    return shots