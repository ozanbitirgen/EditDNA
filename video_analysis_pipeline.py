def analyze_video(
    video_path: str,
    transcript_outline: Optional[Dict[str, Any]] = None,
    video_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    High-level convenience function:
    - run detection, classification, OCR, audio
    - build analysis_json
    - call LLM to get editing blueprint

    Returns: {"analysis_json": ..., "editing_blueprint": ...}
    """
    if video_meta is None:
        # Minimal meta if you don't yet have DB
        duration = get_video_duration(video_path)
        video_meta = {
            "id": os.path.basename(video_path),
            "title": os.path.basename(video_path),
            "duration_seconds": duration,
            "url": None,
            "metrics": {}
        }

    if transcript_outline is None:
        # For now, empty; you’ll fill this once you integrate transcript + outline logic
        transcript_outline = {}

    shots = detect_shots(video_path)
    shots = classify_shots(video_path, shots)
    shots = extract_ocr(video_path, shots)
    audio_segments = extract_audio_segments(video_path)

    analysis_json = build_analysis_json(
        video_meta=video_meta,
        shots=shots,
        audio_segments=audio_segments,
        transcript_outline=transcript_outline
    )

    blueprint = call_llm_blueprint(analysis_json)

    return {
        "analysis_json": analysis_json,
        "editing_blueprint": blueprint
    }


if __name__ == "__main__":
    # Quick manual test
    test_video = "example.mp4"
    if os.path.exists(test_video):
        result = analyze_video(test_video)
        print(json.dumps(result["analysis_json"], indent=2))
        print(json.dumps(result["editing_blueprint"], indent=2))
    else:
        print(f"[INFO] Put a video file named {test_video} next to this script to test.")