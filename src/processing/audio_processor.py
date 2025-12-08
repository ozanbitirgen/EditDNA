"""
Audio processing module for video analysis.
"""
import os
from pydub import AudioSegment
import subprocess
from typing import List
from ..models.data_models import AudioSegmentInfo

def extract_audio_to_wav(video_path: str, out_path: str) -> None:
    """Extract audio from video to WAV file using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        out_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_audio_segments(
    video_path: str,
    min_segment_ms: int = 500
) -> List[AudioSegmentInfo]:
    """
    Extract and analyze audio segments from video.
    
    Args:
        video_path: Path to the video file
        min_segment_ms: Minimum segment length in milliseconds
        
    Returns:
        List of AudioSegmentInfo objects
    """
    print("[INFO] Extracting audio segments ...")
    wav_path = os.path.splitext(video_path)[0] + "_tmp_audio.wav"
    extract_audio_to_wav(video_path, wav_path)
    audio = AudioSegment.from_wav(wav_path)
    duration_ms = len(audio)
    segments = []

    for idx, t_start_ms in enumerate(range(0, duration_ms, min_segment_ms)):
        t_end_ms = min(t_start_ms + min_segment_ms, duration_ms)
        seg = audio[t_start_ms:t_end_ms]
        loudness = seg.dBFS if seg.dBFS != float("-inf") else -80.0

        segments.append(
            AudioSegmentInfo(
                index=idx,
                t_start=t_start_ms / 1000.0,
                t_end=t_end_ms / 1000.0,
                has_speech=True,  # Placeholder - integrate VAD later
                has_music=False,
                has_sfx=False,
                loudness_db=loudness
            )
        )

    try:
        os.remove(wav_path)
    except OSError:
        pass

    return segments