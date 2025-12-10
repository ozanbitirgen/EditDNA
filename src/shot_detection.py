# src/shot_detection.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Dict, Any, Optional
import subprocess
import re
import os

import cv2
import numpy as np

EngineName = Literal["pyscenedetect", "ffmpeg", "transnetv2"]


@dataclass
class Shot:
    index: int
    t_start: float
    t_end: float
    shot_type: Optional[str] = None   # TALKING_HEAD, BROLL, SCREEN, UNKNOWN
    faces_present: Optional[int] = None
    overlay_texts: Optional[list] = None


# ---------- shared helper ---------- #

def get_video_duration(video_path: str) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1",
        video_path,
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)


# ---------- Engine 1: PySceneDetect ---------- #

def detect_shots_pyscenedetect(
    video_path: str,
    threshold: float = 27.0,
    min_scene_len: int = 15,
) -> List[Shot]:
    """
    Use PySceneDetect's ContentDetector.
    threshold: higher -> fewer cuts.
    min_scene_len: minimum length in frames between cuts.
    """
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector

    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len)
    )

    # Downscale for speed
    video_manager.set_downscale_factor()
    video_manager.start()

    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()

    shots: List[Shot] = []
    for idx, (start_time, end_time) in enumerate(scene_list):
        shots.append(
            Shot(
                index=idx,
                t_start=start_time.get_seconds(),
                t_end=end_time.get_seconds(),
            )
        )

    video_manager.release()
    return shots


# ---------- Engine 2: ffmpeg scene filter ---------- #

def detect_shots_ffmpeg(
    video_path: str,
    scene_threshold: float = 0.4,
) -> List[Shot]:
    """
    Use FFmpeg's scene detection:
        select='gt(scene,scene_threshold)',showinfo

    scene_threshold: typical range ~0.3–0.5 (lower -> more cuts)
    """
    duration = get_video_duration(video_path)
    if duration <= 0:
        return []

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-filter:v", f"select='gt(scene,{scene_threshold})',showinfo",
        "-f", "null",
        "-"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    cut_times = [0.0]  # start at 0
    pts_pattern = re.compile(r"pts_time:(\d+\.?\d*)")

    if proc.stderr is not None:
        for line in proc.stderr:
            match = pts_pattern.search(line)
            if match:
                t = float(match.group(1))
                if t > 0:
                    cut_times.append(t)

    proc.wait()

    if cut_times[-1] < duration:
        cut_times.append(duration)

    shots: List[Shot] = []
    for idx in range(len(cut_times) - 1):
        t_start = cut_times[idx]
        t_end = cut_times[idx + 1]
        if (t_end - t_start) < 0.1:  # drop ultra-short noise
            continue
        shots.append(Shot(index=len(shots), t_start=t_start, t_end=t_end))

    return shots


# ---------- Engine 3: TransNetV2 skeleton ---------- #

_transnet_model = None


def get_transnet_model():
    """
    Lazy-load TransNetV2 (or similar) once.
    You implement the real loading in transnetv2_model.py.
    """
    global _transnet_model
    if _transnet_model is None:
        from . import transnetv2_model  # adjust import if needed
        _transnet_model = transnetv2_model.load_model()
    return _transnet_model


def detect_shots_transnet(
    video_path: str,
    probability_threshold: float = 0.5,
    min_gap_frames: int = 5,
) -> List[Shot]:
    """
    Use a TransNetV2-like model to detect shot boundaries.

    You must provide:
    - transnetv2_model.load_model() -> model
    - transnetv2_model.predict_shot_probabilities(model, frames) -> np.ndarray [num_frames]
    """
    from . import transnetv2_model  # adjust path if needed

    model = get_transnet_model()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    if not frames:
        return []

    frames_arr = np.stack(frames, axis=0)  # [num_frames, H, W, 3]
    probs = transnetv2_model.predict_shot_probabilities(model, frames_arr)

    cut_frame_indices = []
    last_cut = -min_gap_frames
    for i, p in enumerate(probs):
        if p >= probability_threshold and (i - last_cut) >= min_gap_frames:
            cut_frame_indices.append(i)
            last_cut = i

    duration = get_video_duration(video_path)
    cut_times = [0.0]
    for fi in cut_frame_indices:
        t = fi / fps
        if t < duration:
            cut_times.append(t)
    if cut_times[-1] < duration:
        cut_times.append(duration)

    shots: List[Shot] = []
    for idx in range(len(cut_times) - 1):
        t_start = cut_times[idx]
        t_end = cut_times[idx + 1]
        if (t_end - t_start) < 0.1:
            continue
        shots.append(Shot(index=len(shots), t_start=t_start, t_end=t_end))

    return shots


# ---------- Normalization & unified dispatcher ---------- #

def _normalize_shots(shots: List[Shot], duration: float, min_length: float = 0.2) -> List[Shot]:
    """Optional: clean up ultra-short segments and clamp to [0, duration]."""
    cleaned: List[Shot] = []
    for s in shots:
        t_start = max(0.0, s.t_start)
        t_end = min(duration, s.t_end)
        if (t_end - t_start) < min_length:
            continue
        cleaned.append(Shot(index=len(cleaned), t_start=t_start, t_end=t_end))
    # ensure last ends at duration
    if cleaned and cleaned[-1].t_end < duration:
        cleaned[-1].t_end = duration
    return cleaned


ENGINE_FUNCS = {
    "pyscenedetect": detect_shots_pyscenedetect,
    "ffmpeg": detect_shots_ffmpeg,
    "transnetv2": detect_shots_transnet,
}


def detect_shots(
    video_path: str,
    engine: EngineName = "pyscenedetect",
    **engine_kwargs: Any,
) -> List[Shot]:
    """
    Unified entrypoint.

    Examples:
        detect_shots("foo.mp4")  # default PySceneDetect
        detect_shots("foo.mp4", engine="ffmpeg", scene_threshold=0.35)
        detect_shots("foo.mp4", engine="transnetv2", probability_threshold=0.6)
    """
    if engine not in ENGINE_FUNCS:
        raise ValueError(f"Unknown shot detection engine: {engine}")

    func = ENGINE_FUNCS[engine]
    raw_shots = func(video_path, **engine_kwargs)

    duration = get_video_duration(video_path)
    shots = _normalize_shots(raw_shots, duration=duration)

    # ensure ordered & reindexed
    shots = sorted(shots, key=lambda s: s.t_start)
    for i, s in enumerate(shots):
        s.index = i

    return shots
