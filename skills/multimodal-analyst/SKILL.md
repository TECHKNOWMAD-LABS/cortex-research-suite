# multimodal-analyst

## Purpose
Cross-modal content analysis. Analyzes text, image URLs, and video URLs together to produce unified analysis. In demo mode, generates synthetic multimodal analysis.

## BettaFish Engine Type
`cross_modal_analysis`

## Phase
Phase 14 — BettaFish-inspired intelligence skills

## Architecture
- **ContentTypeDetector**: Identifies and classifies input content types (text, image, video).
- **ModalityAnalyzer**: Performs per-modality analysis with modality-specific heuristics.
- **CrossModalSynthesizer**: Synthesizes findings across modalities, flags hallucination risks, and produces confidence scores.

## CLI Usage
```bash
python scripts/analyzer.py --input input.json --output results.json --format json
```

## Input
- `--input`: Path to JSON file with structure:
```json
{
  "text": "text content to analyze",
  "image_urls": ["https://example.com/img1.png"],
  "video_urls": ["https://example.com/vid1.mp4"]
}
```

## Output Schema (JSON)
```json
{
  "content_types_detected": ["text", "image", "video"],
  "per_modality_analysis": {
    "text": {"summary": "...", "key_themes": [], "sentiment": "..."},
    "image": [{"url": "...", "description": "...", "objects_detected": []}],
    "video": [{"url": "...", "description": "...", "duration_estimate": "..."}]
  },
  "cross_modal_findings": "...",
  "hallucination_warnings": [],
  "confidence_scores": {"text": 0.0, "image": 0.0, "video": 0.0, "overall": 0.0}
}
```

## Security
- All user input truncated to 50,000 characters before processing.
- HTML content stripped before analysis (stdlib only).
- JSON output validated against expected schema before returning.
- No `pickle`, `eval()`, or `exec()` anywhere.
