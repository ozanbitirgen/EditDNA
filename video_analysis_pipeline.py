# video_analysis_pipeline.py

import os
import json
from typing import Dict, Any, Optional

# ⬇️ adjust the import based on where you put shot_detection.py
# If using src package layout with name "editdna", it might be:
#   from editdna.shot_detection import detect_shots
# If you're running scripts from repo root, this may be enough:
from src.shot_detection import detect_shots   # or just `from shot_detection import detect_shots`

from src.classification import classify_shots        # whatever your actual modules are
from src.ocr import extract_ocr
from src.audio import extract_audio_segments
from src.analysis import build_analysis_json
from src.llm import call_llm_blueprint
from src.utils import get_video_duration             # or wherever you defined it


def analyze_video(
    video_path: str,
    transcript_outline: Optional[Dict[str, Any]] = None,
    video_meta: Optional[Dict[str, Any]] = None,
    shot_engine: str = "pyscenedetect",
    shot_engine_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    High-level convenience function:
    - run detection, classification, OCR, audio
    - build analysis_json
    - call LLM to get editing blueprint

    shot_engine: "pyscenedetect" | "ffmpeg" | "transnetv2"
    shot_engine_kwargs: engine-specific tuning params
    """
    if video_meta is None:
        duration = get_video_duration(video_path)
        video_meta = {
            "id": os.path.basename(video_path),
            "title": os.path.basename(video_path),
            "duration_seconds": duration,
            "url": None,
            "metrics": {},
        }

    if transcript_outline is None:
        transcript_outline = {}

    shot_engine_kwargs = shot_engine_kwargs or {}

    # ⬇️ HERE is the important change
    shots = detect_shots(
        video_path,
        engine=shot_engine,
        **shot_engine_kwargs,
    )

    shots = classify_shots(video_path, shots)
    shots = extract_ocr(video_path, shots)
    audio_segments = extract_audio_segments(video_path)

    analysis_json = build_analysis_json(
        video_meta=video_meta,
        shots=shots,
        audio_segments=audio_segments,
        transcript_outline=transcript_outline,
    )

    blueprint = call_llm_blueprint(analysis_json)

    return {
        "analysis_json": analysis_json,
        "editing_blueprint": blueprint,
    }


if __name__ == "__main__":
    test_video = "example.mp4"
    if os.path.exists(test_video):
        result = analyze_video(
            test_video,
            shot_engine="pyscenedetect",
            shot_engine_kwargs={"threshold": 27.0, "min_scene_len": 15},
        )
        print(json.dumps(result["analysis_json"], indent=2))
        print(json.dumps(result["editing_blueprint"], indent=2))
    else:
        print(f"[INFO] Put a video file named {test_video} next to this script to test.")
