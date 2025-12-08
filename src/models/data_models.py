"""
Data models for the EditDNA project.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class Shot:
    """Represents a video shot segment."""
    index: int
    t_start: float
    t_end: float
    shot_type: Optional[str] = None   # TALKING_HEAD, BROLL, SCREEN, UNKNOWN
    faces_present: Optional[int] = None
    overlay_texts: Optional[List[Dict[str, Any]]] = None

@dataclass
class AudioSegmentInfo:
    """Represents an audio segment with classification."""
    index: int
    t_start: float
    t_end: float
    has_speech: bool
    has_music: bool
    has_sfx: bool
    loudness_db: float

@dataclass
class OverlayTextBlock:
    """Represents a block of overlay text in a video."""
    t_start: float
    t_end: float
    text: str
    position: str  # TOP, BOTTOM, CENTER, UNKNOWN
    is_caption: bool