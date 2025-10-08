#!/usr/bin/env python3
"""
Classify ALL frames CONCURRENTLY using Claude VLM with async processing.
Much faster than sequential processing - can run 5-10 frames in parallel.
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import json
from datetime import datetime
import asyncio
from typing import List, Dict, Tuple

# Add subbu to path to import Claude client
sys.path.insert(0, str(Path(__file__).parent.parent / 'subbu'))

import anthropic


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


def encode_image(image: np.ndarray, quality: int = 85) -> str:
    """
    Encode numpy image as base64 JPEG.

    Parameters
    ----------
    image : np.ndarray
        Image array (RGB)
    quality : int
        JPEG quality (1-100)

    Returns
    -------
    str
        Base64 encoded JPEG
    """
    import base64
    import io
    from PIL import Image

    # Convert to PIL
    pil_image = Image.fromarray(image)

    # Convert to JPEG
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)

    # Encode base64
    encoded = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def load_cell_counts(tracks_file='nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt'):
    """
    Load cell counts per timepoint from tracks file.

    Returns
    -------
    dict
        Mapping from timepoint to cell count
    """
    tracks_df = pd.read_csv(tracks_file, sep='\t')
    cell_counts = tracks_df.groupby('t').size().to_dict()
    return cell_counts


async def classify_single_frame(
    client: anthropic.AsyncAnthropic,
    frame_idx: int,
    frame_path: Path,
    timepoint: int,
    cell_count: int,
    semaphore: asyncio.Semaphore
) -> Dict:
    """
    Classify a single frame asynchronously.

    Parameters
    ----------
    client : AsyncAnthropic
        Async Anthropic client
    frame_idx : int
        Frame index
    frame_path : Path
        Path to frame image
    timepoint : int
        Time in minutes
    cell_count : int
        Number of tracked cells
    semaphore : asyncio.Semaphore
        Semaphore to limit concurrent requests

    Returns
    -------
    dict
        Classification result
    """
    async with semaphore:
        try:
            # Load image
            image = cv2.imread(str(frame_path))
            if image is None:
                raise ValueError(f"Could not load image {frame_path}")

            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Encode image
            image_b64 = encode_image(image_rgb)

            # Build prompt
            prompt = CLASSIFICATION_PROMPT.format(
                timepoint=timepoint,
                cell_count=cell_count
            )

            # Build message content
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64,
                    },
                }
            ]

            # Make API call
            response = await client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                temperature=1.0,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}]
            )

            # Extract text response
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            # Return classification
            return {
                'timepoint_minutes': timepoint,
                'frame_index': frame_idx,
                'frame_path': str(frame_path),
                'cell_count': cell_count,
                'response': response_text,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }

        except Exception as e:
            print(f"\nERROR classifying frame {frame_idx}: {e}")
            return {
                'timepoint_minutes': timepoint,
                'frame_index': frame_idx,
                'frame_path': str(frame_path),
                'cell_count': cell_count,
                'response': f"ERROR: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'success': False
            }


async def classify_batch(
    client: anthropic.AsyncAnthropic,
    frames_to_process: List[Tuple[int, Path, int, int]],
    max_concurrent: int,
    progress_callback=None
) -> List[Dict]:
    """
    Classify a batch of frames concurrently.

    Parameters
    ----------
    client : AsyncAnthropic
        Async Anthropic client
    frames_to_process : list
        List of (frame_idx, frame_path, timepoint, cell_count) tuples
    max_concurrent : int
        Maximum concurrent requests
    progress_callback : callable, optional
        Callback for progress updates

    Returns
    -------
    list
        List of classification results
    """
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)

    # Create tasks for all frames
    tasks = [
        classify_single_frame(
            client, frame_idx, frame_path, timepoint, cell_count, semaphore
        )
        for frame_idx, frame_path, timepoint, cell_count in frames_to_process
    ]

    # Process with progress tracking
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        if progress_callback:
            progress_callback(len(results), len(tasks), result)

    return results


async def classify_all_frames_async(
    frames_dir='1_png',
    tracks_file='nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt',
    output_file='embryo_classifications_all.json',
    api_key=None,
    resume=True,
    max_concurrent=5
):
    """
    Classify ALL frames concurrently.

    Parameters
    ----------
    frames_dir : str
        Directory containing annotated PNG frames
    tracks_file : str
        Path to tracks.txt file
    output_file : str
        JSON file to save classifications
    api_key : str, optional
        Anthropic API key
    resume : bool
        If True, skip already-classified frames
    max_concurrent : int
        Maximum concurrent API requests (default: 5)
    """

    # Get API key
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it with: set ANTHROPIC_API_KEY=your-key-here"
            )

    # Initialize async client
    print("Initializing async Claude client...")
    client = anthropic.AsyncAnthropic(api_key=api_key)

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
        print(f"Already classified {len(classified_indices)} frames")

    # Build list of frames to process
    frames_to_process = []
    for frame_idx, frame_path in enumerate(all_frames):
        if frame_idx in classified_indices:
            continue
        timepoint = frame_idx
        cell_count = cell_counts.get(timepoint, "unknown")
        frames_to_process.append((frame_idx, frame_path, timepoint, cell_count))

    if len(frames_to_process) == 0:
        print("All frames already classified!")
        return classifications

    # Estimate cost
    estimated_tokens = len(frames_to_process) * 2400
    estimated_cost = estimated_tokens / 1_000_000 * 3.75
    print(f"\nProcessing {len(frames_to_process)} frames with {max_concurrent} concurrent requests")
    print(f"Estimated cost: ~${estimated_cost:.2f}")
    print(f"Estimated time: ~{len(frames_to_process) / max_concurrent * 3:.0f} seconds")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return classifications

    # Track results as they come in
    completed_results = []

    # Progress callback
    def progress_callback(completed, total, result):
        pct = (completed / total) * 100
        status = "✓" if result['success'] else "✗"
        print(f"[{completed}/{total} ({pct:.1f}%)] {status} Frame {result['frame_index']} @ t={result['timepoint_minutes']}min")

        # Add result to list
        completed_results.append(result)

        # Save progress every 10 frames
        if completed % 10 == 0:
            all_results = classifications + completed_results
            all_results.sort(key=lambda x: x['frame_index'])
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"  → Saved progress to {output_file}")

    # Process frames
    print("\nClassifying frames...\n")
    new_results = await classify_batch(
        client, frames_to_process, max_concurrent, progress_callback
    )

    # Combine with existing classifications
    all_results = classifications + new_results
    all_results.sort(key=lambda x: x['frame_index'])

    # Save final results
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    # Summary
    successful = sum(1 for r in new_results if r['success'])
    failed = len(new_results) - successful

    print(f"\n{'='*60}")
    print(f"COMPLETE!")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total frames: {len(all_results)}")
    print(f"  Results saved to: {output_file}")
    print(f"{'='*60}")

    return all_results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Classify ALL C. elegans embryo frames CONCURRENTLY using Claude VLM'
    )
    parser.add_argument(
        '--frames-dir',
        default='1_png',
        help='Directory containing PNG frames (default: 1_png)'
    )
    parser.add_argument(
        '--tracks-file',
        default='nih-ls/nih_diSPIM_deconv_1/tracks/tracks.txt',
        help='Path to tracks.txt file'
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
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Maximum concurrent requests (default: 5, increase for faster processing)'
    )

    args = parser.parse_args()

    # Run async function
    asyncio.run(classify_all_frames_async(
        frames_dir=args.frames_dir,
        tracks_file=args.tracks_file,
        output_file=args.output,
        api_key=args.api_key,
        resume=not args.no_resume,
        max_concurrent=args.max_concurrent
    ))


if __name__ == '__main__':
    main()
