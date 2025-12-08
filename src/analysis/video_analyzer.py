"""
Video analysis and statistics generation.
"""
from typing import Dict, Any, List
import numpy as np
from ..models.data_models import Shot, AudioSegmentInfo

def build_analysis_json(
    video_meta: Dict[str, Any],
    shots: List[Shot],
    audio_segments: List[AudioSegmentInfo],
    transcript_outline: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build comprehensive analysis JSON from processed data.
    
    Args:
        video_meta: Video metadata
        shots: List of processed shots
        audio_segments: List of audio segments
        transcript_outline: Transcript data
        
    Returns:
        Analysis results as a dictionary
    """
    duration = video_meta.get("duration_seconds", 0.0)
    shot_lengths = [s.t_end - s.t_start for s in shots] or [0.0]
    total_time = sum(shot_lengths) or 1.0

    # Calculate statistics
    def ratio_for_type(t):
        return float(sum(
            (s.t_end - s.t_start) for s in shots if s.shot_type == t
        ) / total_time)

    # Build the analysis dictionary
    analysis = {
        "video": {
            "id": video_meta.get("id"),
            "title": video_meta.get("title"),
            "duration_seconds": duration,
            "url": video_meta.get("url"),
            "metrics": video_meta.get("metrics", {})
        },
        "edit_stats": {
            "total_shots": len(shots),
            "avg_shot_length": float(np.mean(shot_lengths)),
            "median_shot_length": float(np.median(shot_lengths)),
            "talking_head_ratio": ratio_for_type("TALKING_HEAD"),
            "broll_ratio": ratio_for_type("BROLL"),
            "screen_record_ratio": ratio_for_type("SCREEN") if any(s.shot_type == "SCREEN" for s in shots) else 0.0,
        },
        "shots": [
            {
                "index": s.index,
                "t_start": s.t_start,
                "t_end": s.t_end,
                "shot_type": s.shot_type,
                "faces_present": s.faces_present,
                "overlay_text": s.overlay_texts or []
            }
            for s in shots
        ],
        "audio_pattern": {
            "segments": [{
                "index": seg.index,
                "t_start": seg.t_start,
                "t_end": seg.t_end,
                "has_speech": seg.has_speech,
                "has_music": seg.has_music,
                "has_sfx": seg.has_sfx,
                "loudness_db": seg.loudness_db
            } for seg in audio_segments]
        },
        "transcript_outline": transcript_outline or {}
    }

    return analysis