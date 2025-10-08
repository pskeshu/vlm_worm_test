#!/usr/bin/env python3
"""
Classify ALL frames (not just sampled) using Claude VLM.
Includes actual cell counts from tracking data.
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import json
from datetime import datetime
from tqdm import tqdm

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
**Tracked cell count**: {cell_count} cells

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


def load_cell_counts(tracks_file='nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt'):
    """
    Load cell counts per timepoint from tracks file.

    Returns
    -------
    dict
        Mapping from timepoint to cell count
    """
    tracks_df = pd.read_csv(tracks_file, sep='\t')

    # Count cells per timepoint
    cell_counts = tracks_df.groupby('t').size().to_dict()

    return cell_counts


def classify_all_frames(
    frames_dir='1_png',
    tracks_file='nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt',
    output_file='embryo_classifications_all.json',
    api_key=None,
    resume=True
):
    """
    Classify ALL embryo frames (not just sampled).

    Parameters
    ----------
    frames_dir : str
        Directory containing annotated PNG frames
    tracks_file : str
        Path to tracks.txt file
    output_file : str
        JSON file to save classifications
    api_key : str, optional
        Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
    resume : bool
        If True, skip already-classified frames
    """

    # Get API key
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it with: set ANTHROPIC_API_KEY=your-key-here"
            )

    # Initialize Claude client
    print("Initializing Claude client...")
    client = ClaudeClient(api_key=api_key, max_tokens=2048)

    # Load cell counts from tracks
    print(f"Loading cell counts from {tracks_file}...")
    cell_counts = load_cell_counts(tracks_file)
    print(f"Loaded cell counts for {len(cell_counts)} timepoints")

    # Load frames
    print(f"Loading frames from {frames_dir}...")
    frames_path = Path(frames_dir)
    all_frames = sorted(frames_path.glob('frame_*.png'))
    print(f"Found {len(all_frames)} frames to analyze")

    # Load existing classifications if resuming
    classifications = []
    classified_indices = set()

    if resume and Path(output_file).exists():
        print(f"Resuming from {output_file}...")
        with open(output_file, 'r') as f:
            classifications = json.load(f)
        classified_indices = {c['frame_index'] for c in classifications}
        print(f"Already classified {len(classified_indices)} frames, {len(all_frames) - len(classified_indices)} remaining")

    # Estimate cost
    frames_to_process = len(all_frames) - len(classified_indices)
    estimated_tokens = frames_to_process * 2400
    estimated_cost = estimated_tokens / 1_000_000 * 3.75  # Rough estimate
    print(f"\nEstimated cost for remaining {frames_to_process} frames:")
    print(f"  Tokens: ~{estimated_tokens:,}")
    print(f"  Cost: ~${estimated_cost:.2f}")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Process each frame
    for frame_idx, frame_path in enumerate(tqdm(all_frames, desc="Classifying frames")):
        # Skip if already classified
        if frame_idx in classified_indices:
            continue

        timepoint = frame_idx  # Since temporal resolution is 1 min/frame
        cell_count = cell_counts.get(timepoint, "unknown")

        # Load image
        image = cv2.imread(str(frame_path))
        if image is None:
            print(f"ERROR: Could not load image {frame_path}")
            continue

        # Convert BGR to RGB for Claude
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Build prompt
        prompt = CLASSIFICATION_PROMPT.format(
            timepoint=timepoint,
            cell_count=cell_count
        )

        # Query Claude
        try:
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

            # Save classification
            classification = {
                'timepoint_minutes': timepoint,
                'frame_index': frame_idx,
                'frame_path': str(frame_path),
                'cell_count': cell_count,
                'response': response_text,
                'timestamp': datetime.now().isoformat()
            }
            classifications.append(classification)

            # Save after each classification (for resume capability)
            with open(output_file, 'w') as f:
                json.dump(classifications, f, indent=2)

        except Exception as e:
            print(f"\nERROR classifying frame {frame_idx}: {e}")
            print("Saving progress and continuing...")
            with open(output_file, 'w') as f:
                json.dump(classifications, f, indent=2)
            continue

    # Final summary
    print(f"\n{'='*60}")
    print(f"COMPLETE: Analyzed {len(classifications)} frames")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")

    return classifications


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Classify ALL C. elegans embryo frames using Claude VLM'
    )
    parser.add_argument(
        '--frames-dir',
        default='1_png',
        help='Directory containing PNG frames (default: 1_png)'
    )
    parser.add_argument(
        '--tracks-file',
        default='nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt',
        help='Path to tracks.txt file (default: nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt)'
    )
    parser.add_argument(
        '--output',
        default='embryo_classifications_all.json',
        help='Output JSON file (default: embryo_classifications_all.json)'
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start from scratch (ignore existing classifications)'
    )

    args = parser.parse_args()

    classify_all_frames(
        frames_dir=args.frames_dir,
        tracks_file=args.tracks_file,
        output_file=args.output,
        api_key=args.api_key,
        resume=not args.no_resume
    )
