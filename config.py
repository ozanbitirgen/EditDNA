SHOT_ENGINE_CONFIGS = {
    "default": {
        "engine": "pyscenedetect",
        "params": {"threshold": 27.0, "min_scene_len": 15},
    },
    "fast_ffmpeg": {
        "engine": "ffmpeg",
        "params": {"scene_threshold": 0.4},
    },
    "high_precision": {
        "engine": "transnetv2",
        "params": {"probability_threshold": 0.6, "min_gap_frames": 5},
    },
}
