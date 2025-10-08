#!/usr/bin/env python3
"""
Classify C. elegans embryo developmental stages using Claude VLM.
Samples frames every 10 minutes and asks Claude to classify the developmental stage.
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
import json
from datetime import datetime

# Add subbu to path to import Claude client
sys.path.insert(0, str(Path(__file__).parent.parent / 'subbu'))

from subbu.claude.client import ClaudeClient


SYSTEM_PROMPT = """You are an expert developmental biologist specializing in C. elegans embryogenesis.

Your task is to classify embryo developmental stages from microscope images with nucleus tracking data.

You have deep knowledge of:
- C. elegans cell lineage and division patterns
- Characteristic morphological features at each developmental stage
- Expected cell counts at different time points
- Normal vs abnormal development

Be precise, analytical, and honest about uncertainty."""


CLASSIFICATION_PROMPT = """You are analyzing a time-lapse series of a developing C. elegans embryo.

This is a max projection image showing all nuclei (tracked cells shown with green circles).

**Time point**: {timepoint} minutes into development
**Current cell count**: {cell_count} cells

Please classify the developmental stage of this embryo and provide your reasoning.

## Classification Categories
- **1-cell**: Single cell, often with visible pronuclei
- **2-cell**: Two cells after first division (P1 and AB)
- **4-cell**: Four cells (ABa, ABp, EMS, P2)
- **8-cell**: Eight cells
- **~14-cell**: Approximately 12-14 cells
- **~24-cell**: Approximately 24-28 cells
- **~44-cell**: Approximately 44 cells
- **~90-cell**: Approximately 90 cells, gastrulation begins
- **~190-cell**: Approximately 190 cells
- **~350-cell**: Approximately 350 cells
- **comma**: Comma stage (~550 cells)
- **1.5-fold**: 1.5-fold elongation stage
- **2-fold**: 2-fold elongation stage
- **3-fold**: 3-fold elongation stage (pre-hatch)

## Your Response Should Include:

1. **Developmental Stage**: Your classification (e.g., "4-cell", "~90-cell", "comma", etc.)

2. **Confidence**: Your confidence in this classification (0.0 to 1.0)

3. **Reasoning**:
   - What visual features led to this classification?
   - Does the cell count match expectations for this stage?
   - Does the overall morphology match this stage?
   - Are there any characteristic features visible (e.g., cell arrangement, embryo shape)?

4. **Concerns or Uncertainties**:
   - Any ambiguities in the image?
   - Alternative classifications that were considered?
   - Quality issues affecting classification?

Please be thorough in your reasoning and honest about uncertainties."""


def load_frames_with_annotations(frames_dir='1_png', sample_interval=10):
    """
    Load frames at specified interval

    Parameters
    ----------
    frames_dir : str
        Directory containing PNG frames
    sample_interval : int
        Sample every N minutes (default: 10)

    Returns
    -------
    list
        List of tuples (timepoint, frame_path)
    """
    frames_path = Path(frames_dir)

    if not frames_path.exists():
        raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

    # Get all frames
    all_frames = sorted(frames_path.glob('frame_*.png'))

    # Sample every N frames (since temporal resolution is 1 min/frame)
    sampled_frames = []
    for i in range(0, len(all_frames), sample_interval):
        timepoint = i  # minutes
        sampled_frames.append((timepoint, all_frames[i]))

    return sampled_frames


def extract_cell_count_from_image(image_path):
    """
    Try to extract cell count from the text annotation in the image.
    This is a simple approach - reads the image and looks for "Cells: N" text.

    Returns None if unable to extract.
    """
    # For now, we'll parse it from the filename pattern or return None
    # In practice, you might OCR the image or track it separately
    return None


def classify_embryo_timeseries(
    frames_dir='1_png',
    sample_interval=10,
    output_file='embryo_classifications.json',
    api_key=None
):
    """
    Classify embryo developmental stages across time series

    Parameters
    ----------
    frames_dir : str
        Directory containing annotated PNG frames
    sample_interval : int
        Sample every N minutes
    output_file : str
        JSON file to save classifications
    api_key : str, optional
        Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
    """

    # Get API key
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it with: export ANTHROPIC_API_KEY=your-key-here"
            )

    # Initialize Claude client
    print("Initializing Claude client...")
    client = ClaudeClient(api_key=api_key, max_tokens=2048)

    # Load sampled frames
    print(f"Loading frames from {frames_dir}, sampling every {sample_interval} minutes...")
    sampled_frames = load_frames_with_annotations(frames_dir, sample_interval)
    print(f"Found {len(sampled_frames)} frames to analyze")

    # Track all classifications
    classifications = []

    # Process each frame
    for idx, (timepoint, frame_path) in enumerate(sampled_frames):
        print(f"\n{'='*60}")
        print(f"Analyzing frame {idx+1}/{len(sampled_frames)}")
        print(f"Time: {timepoint} minutes")
        print(f"Frame: {frame_path.name}")
        print(f"{'='*60}")

        # Load image
        image = cv2.imread(str(frame_path))
        if image is None:
            print(f"ERROR: Could not load image {frame_path}")
            continue

        # Convert BGR to RGB for Claude
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Extract cell count (if available from annotation)
        # For now, we'll parse from track data or estimate
        # You could also use OCR to read the "Cells: N" text from image
        cell_count = "visible in image"  # Placeholder

        # Build prompt
        prompt = CLASSIFICATION_PROMPT.format(
            timepoint=timepoint,
            cell_count=cell_count
        )

        # Query Claude
        print("Sending to Claude...")
        response = client.query(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            images=[image_rgb]
        )

        # Extract text response
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        print("\n--- Claude's Response ---")
        print(response_text)
        print("--- End Response ---\n")

        # Save classification
        classification = {
            'timepoint_minutes': timepoint,
            'frame_index': idx * sample_interval,
            'frame_path': str(frame_path),
            'response': response_text,
            'timestamp': datetime.now().isoformat()
        }
        classifications.append(classification)

        # Save intermediate results after each classification
        with open(output_file, 'w') as f:
            json.dump(classifications, f, indent=2)
        print(f"Saved to {output_file}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"COMPLETE: Analyzed {len(classifications)} timepoints")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")

    return classifications


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Classify C. elegans embryo developmental stages using Claude VLM'
    )
    parser.add_argument(
        '--frames-dir',
        default='1_png',
        help='Directory containing PNG frames (default: 1_png)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Sample every N minutes (default: 10)'
    )
    parser.add_argument(
        '--output',
        default='embryo_classifications.json',
        help='Output JSON file (default: embryo_classifications.json)'
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )

    args = parser.parse_args()

    classify_embryo_timeseries(
        frames_dir=args.frames_dir,
        sample_interval=args.interval,
        output_file=args.output,
        api_key=args.api_key
    )
