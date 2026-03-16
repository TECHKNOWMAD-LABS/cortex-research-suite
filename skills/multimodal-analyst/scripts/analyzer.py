#!/usr/bin/env python3
"""
multimodal-analyst: Cross-modal content analysis.
Phase 14 — BettaFish-inspired intelligence skills.
BettaFish engine type: cross_modal_analysis

Analyzes text, image URLs, and video URLs together to produce unified
analysis. In demo mode, generates synthetic multimodal analysis.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

MAX_INPUT_CHARS = 50000

# ---------- Security helpers ----------

class _HTMLStripper(HTMLParser):
    """Strip HTML tags using stdlib html.parser."""

    def __init__(self):
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def strip_html(text: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


def sanitize_input(text: str) -> str:
    """Truncate and strip HTML from user input."""
    text = text[:MAX_INPUT_CHARS]
    return strip_html(text)


# ---------- Output schema validation ----------

EXPECTED_KEYS = {
    "content_types_detected": list,
    "per_modality_analysis": dict,
    "cross_modal_findings": str,
    "hallucination_warnings": list,
    "confidence_scores": dict,
}


def validate_output(data: Dict[str, Any]) -> bool:
    """Validate output JSON against expected schema."""
    for key, expected_type in EXPECTED_KEYS.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            return False
    # Validate confidence_scores sub-keys
    required_score_keys = {"text", "image", "video", "overall"}
    if not required_score_keys.issubset(set(data.get("confidence_scores", {}).keys())):
        return False
    return True


# ---------- Core classes ----------

class ContentTypeDetector:
    """Identifies and classifies input content types."""

    def detect(self, input_data: Dict[str, Any]) -> List[str]:
        types = []
        text = input_data.get("text", "")
        if text and isinstance(text, str) and text.strip():
            types.append("text")
        image_urls = input_data.get("image_urls", [])
        if image_urls and isinstance(image_urls, list) and len(image_urls) > 0:
            types.append("image")
        video_urls = input_data.get("video_urls", [])
        if video_urls and isinstance(video_urls, list) and len(video_urls) > 0:
            types.append("video")
        return types


class ModalityAnalyzer:
    """Performs per-modality analysis with synthetic demo output."""

    def analyze_text(self, text: str) -> Dict[str, Any]:
        cleaned = sanitize_input(text)
        words = cleaned.split()
        word_count = len(words)
        # Simple keyword-based sentiment heuristic
        positive_words = {"good", "great", "excellent", "positive", "success", "benefit"}
        negative_words = {"bad", "terrible", "risk", "failure", "threat", "danger"}
        lower_words = {w.lower().strip(".,!?") for w in words}
        pos = len(lower_words & positive_words)
        neg = len(lower_words & negative_words)
        if pos > neg:
            sentiment = "positive"
        elif neg > pos:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Extract key themes (top repeated non-trivial words)
        freq: Dict[str, int] = {}
        stop = {"the", "a", "an", "is", "are", "was", "were", "in", "on",
                "at", "to", "for", "of", "and", "or", "but", "with", "this",
                "that", "it", "be", "as", "by", "from", "not", "no"}
        for w in words:
            lw = w.lower().strip(".,!?;:'\"")
            if len(lw) > 2 and lw not in stop:
                freq[lw] = freq.get(lw, 0) + 1
        key_themes = sorted(freq, key=freq.get, reverse=True)[:5]

        return {
            "summary": f"Text analysis: {word_count} words processed.",
            "key_themes": key_themes,
            "sentiment": sentiment,
        }

    def analyze_images(self, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        for url in urls:
            sanitized_url = sanitize_input(url)
            seed = hashlib.sha256(sanitized_url.encode()).hexdigest()[:8]
            results.append({
                "url": sanitized_url,
                "description": f"[DEMO] Synthetic image analysis for {sanitized_url} (seed={seed}).",
                "objects_detected": [
                    f"object_{seed[:4]}", f"object_{seed[4:]}"
                ],
            })
        return results

    def analyze_videos(self, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        for url in urls:
            sanitized_url = sanitize_input(url)
            seed = hashlib.sha256(sanitized_url.encode()).hexdigest()[:8]
            duration_est = 30 + (int(seed, 16) % 300)
            results.append({
                "url": sanitized_url,
                "description": f"[DEMO] Synthetic video analysis for {sanitized_url} (seed={seed}).",
                "duration_estimate": f"{duration_est}s",
            })
        return results


class CrossModalSynthesizer:
    """Synthesizes findings across modalities."""

    def synthesize(
        self,
        content_types: List[str],
        text_analysis: Optional[Dict[str, Any]],
        image_analysis: List[Dict[str, Any]],
        video_analysis: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        per_modality: Dict[str, Any] = {}
        hallucination_warnings: List[str] = []
        confidence_scores: Dict[str, float] = {
            "text": 0.0,
            "image": 0.0,
            "video": 0.0,
            "overall": 0.0,
        }

        if "text" in content_types and text_analysis:
            per_modality["text"] = text_analysis
            confidence_scores["text"] = 0.85
        else:
            hallucination_warnings.append(
                "No text content provided; text modality scores are zero."
            )

        if "image" in content_types and image_analysis:
            per_modality["image"] = image_analysis
            confidence_scores["image"] = 0.60
            hallucination_warnings.append(
                "Image analysis is synthetic (demo mode). "
                "Object detection results are not from a real vision model."
            )
        else:
            confidence_scores["image"] = 0.0

        if "video" in content_types and video_analysis:
            per_modality["video"] = video_analysis
            confidence_scores["video"] = 0.45
            hallucination_warnings.append(
                "Video analysis is synthetic (demo mode). "
                "Duration and content descriptions are estimated."
            )
        else:
            confidence_scores["video"] = 0.0

        # Overall confidence is weighted average of active modalities
        active = [(k, v) for k, v in confidence_scores.items()
                  if k != "overall" and v > 0.0]
        if active:
            confidence_scores["overall"] = round(
                sum(v for _, v in active) / len(active), 2
            )

        cross_modal_findings = (
            f"Cross-modal analysis across {len(content_types)} modalities: "
            f"{', '.join(content_types)}. "
        )
        if text_analysis and text_analysis.get("key_themes"):
            cross_modal_findings += (
                f"Text themes ({', '.join(text_analysis['key_themes'][:3])}) "
                f"may correlate with visual content. "
            )
        cross_modal_findings += (
            f"Overall confidence: {confidence_scores['overall']}."
        )

        result = {
            "content_types_detected": content_types,
            "per_modality_analysis": per_modality,
            "cross_modal_findings": cross_modal_findings,
            "hallucination_warnings": hallucination_warnings,
            "confidence_scores": confidence_scores,
        }

        if not validate_output(result):
            raise RuntimeError("Output validation failed against expected schema.")

        return result


# ---------- CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="multimodal-analyst: Cross-modal content analysis"
    )
    parser.add_argument(
        "--input", required=True, type=str,
        help="Path to input JSON file"
    )
    parser.add_argument(
        "--output", required=True, type=str,
        help="Output file path for JSON report"
    )
    parser.add_argument(
        "--format", default="json", choices=["json"],
        help="Output format (default: json)"
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        raw = f.read()[:MAX_INPUT_CHARS]
        input_data = json.loads(raw)

    if not isinstance(input_data, dict):
        print("Error: Input JSON must be an object.", file=sys.stderr)
        sys.exit(1)

    detector = ContentTypeDetector()
    analyzer = ModalityAnalyzer()
    synthesizer = CrossModalSynthesizer()

    content_types = detector.detect(input_data)

    text_analysis = None
    image_analysis: List[Dict[str, Any]] = []
    video_analysis: List[Dict[str, Any]] = []

    if "text" in content_types:
        text_analysis = analyzer.analyze_text(input_data["text"])
    if "image" in content_types:
        image_analysis = analyzer.analyze_images(input_data["image_urls"])
    if "video" in content_types:
        video_analysis = analyzer.analyze_videos(input_data["video_urls"])

    report = synthesizer.synthesize(
        content_types, text_analysis, image_analysis, video_analysis
    )

    output_json = json.dumps(report, indent=2, ensure_ascii=False)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output_json)

    print(f"Multimodal analysis written to {args.output}")
    print(f"Content types detected: {content_types}")
    print(f"Overall confidence: {report['confidence_scores']['overall']}")


if __name__ == "__main__":
    main()
