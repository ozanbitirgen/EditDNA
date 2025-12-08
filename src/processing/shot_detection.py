"""
Shot detection module for video analysis.
"""
from typing import List
import subprocess
from ..models.data_models import Shot

def get_video_duration(video_path: str) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1",
        video_path,
    ]
    try:
        out = subprocess.check_output(cmd).decode().strip()
        return float(out)
    except Exception as e:
        print(f"[WARN] Could not get duration for {video_path}: {e}")
        return 0.0

def detect_shots(video_path: str, threshold: float = 0.4) -> List[Shot]:
    """
    Detect shots in a video.
    
    Args:
        video_path: Path to the video file
        threshold: Threshold for shot detection (0.0-1.0)
        
    Returns:
        List of Shot objects with t_start/t_end filled
    """
    print(f"[INFO] Detecting shots for {video_path} ...")
    duration = get_video_duration(video_path)
    shots = []
    
    if duration <= 0:
        return shots

    # TODO: Replace with real shot boundary detection
    fake_shot_length = 2.5
    for idx, t_start in enumerate([i * fake_shot_length for i in range(int(duration / fake_shot_length) + 1)]):
        t_end = min(t_start + fake_shot_length, duration)
        if t_start < t_end:  # Ensure we don't create zero-length shots
            shots.append(Shot(
                index=idx,
                t_start=t_start,
                t_end=t_end
            ))

    print(f"[INFO] Generated {len(shots)} shots")
    return shots