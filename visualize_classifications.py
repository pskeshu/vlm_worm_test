#!/usr/bin/env python3
"""
Visualize embryo classification results from Claude VLM analysis.
Creates annotated video/frames showing Claude's predictions alongside the images.
"""

import json
import re
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm


def parse_classification_response(response_text):
    """
    Parse Claude's response to extract stage, confidence, and reasoning.

    Returns
    -------
    dict
        Parsed classification with keys: stage, confidence, reasoning
    """
    result = {
        'stage': 'Unknown',
        'confidence': 0.0,
        'reasoning': ''
    }

    # Try to extract stage
    stage_match = re.search(r'\*\*Developmental Stage\*\*:?\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE)
    if stage_match:
        result['stage'] = stage_match.group(1).strip()

    # Try to extract confidence
    conf_match = re.search(r'\*\*Confidence\*\*:?\s*([0-9.]+)', response_text, re.IGNORECASE)
    if conf_match:
        result['confidence'] = float(conf_match.group(1))

    # Try to extract reasoning section
    reasoning_match = re.search(r'\*\*Reasoning\*\*:?\s*\n(.+?)(?:\n\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
    if reasoning_match:
        result['reasoning'] = reasoning_match.group(1).strip()
    else:
        # Fall back to full response
        result['reasoning'] = response_text[:200] + '...' if len(response_text) > 200 else response_text

    return result


def create_info_panel(width, height, timepoint, classification, bg_color=(40, 40, 40)):
    """
    Create an information panel with classification details.

    Parameters
    ----------
    width : int
        Panel width
    height : int
        Panel height
    timepoint : int
        Time in minutes
    classification : dict
        Parsed classification data
    bg_color : tuple
        Background color (BGR)

    Returns
    -------
    np.ndarray
        Info panel image
    """
    panel = np.full((height, width, 3), bg_color, dtype=np.uint8)

    # Text parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    white = (255, 255, 255)
    green = (0, 255, 0)
    yellow = (0, 255, 255)

    y_pos = 30
    line_height = 35

    # Title
    cv2.putText(panel, "Claude VLM Classification", (10, y_pos),
                font, 0.7, white, 2, cv2.LINE_AA)
    y_pos += line_height + 10

    # Time
    cv2.putText(panel, f"Time: {timepoint} min", (10, y_pos),
                font, 0.6, white, 1, cv2.LINE_AA)
    y_pos += line_height

    # Stage
    cv2.putText(panel, f"Stage: {classification['stage']}", (10, y_pos),
                font, 0.7, green, 2, cv2.LINE_AA)
    y_pos += line_height + 5

    # Confidence
    conf_pct = int(classification['confidence'] * 100)
    conf_text = f"Confidence: {conf_pct}%"
    cv2.putText(panel, conf_text, (10, y_pos),
                font, 0.6, yellow, 1, cv2.LINE_AA)
    y_pos += line_height + 10

    # Draw confidence bar
    bar_width = width - 40
    bar_height = 20
    bar_x = 20
    bar_y = y_pos

    # Background bar
    cv2.rectangle(panel, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                  (100, 100, 100), -1)

    # Filled portion based on confidence
    filled_width = int(bar_width * classification['confidence'])
    color = green if classification['confidence'] > 0.8 else yellow if classification['confidence'] > 0.5 else (0, 100, 255)
    cv2.rectangle(panel, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height),
                  color, -1)

    y_pos += bar_height + 25

    # Reasoning (word wrapped)
    cv2.putText(panel, "Reasoning:", (10, y_pos),
                font, 0.5, white, 1, cv2.LINE_AA)
    y_pos += 25

    reasoning = classification['reasoning']
    max_chars_per_line = 45
    words = reasoning.split()
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) > max_chars_per_line:
            if current_line:
                cv2.putText(panel, current_line, (10, y_pos),
                           font, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
                y_pos += 20
                current_line = word
            else:
                # Word is too long, just add it anyway
                cv2.putText(panel, word, (10, y_pos),
                           font, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
                y_pos += 20
                current_line = ""
        else:
            current_line = test_line

        if y_pos > height - 30:
            current_line += "..."
            break

    if current_line:
        cv2.putText(panel, current_line, (10, y_pos),
                   font, 0.4, (200, 200, 200), 1, cv2.LINE_AA)

    return panel


def create_visualization(
    classifications_file='embryo_classifications.json',
    frames_dir='1_png',
    output_video='embryo_classifications_annotated.mp4',
    output_frames_dir='2_classified_png',
    panel_width=500,
    fps=2,
    create_video=True,
    create_frames=True
):
    """
    Create visualization of classification results.

    Parameters
    ----------
    classifications_file : str
        JSON file with classifications
    frames_dir : str
        Directory with original PNG frames
    output_video : str
        Output video filename
    output_frames_dir : str
        Directory for annotated frames
    panel_width : int
        Width of info panel
    fps : int
        Frames per second for video
    create_video : bool
        Whether to create video
    create_frames : bool
        Whether to save individual frames
    """

    # Load classifications
    print(f"Loading classifications from {classifications_file}...")
    with open(classifications_file, 'r') as f:
        classifications = json.load(f)

    print(f"Found {len(classifications)} classifications")

    if len(classifications) == 0:
        print("No classifications found!")
        return

    # Create output directory for frames if needed
    if create_frames:
        output_frames_path = Path(output_frames_dir)
        output_frames_path.mkdir(parents=True, exist_ok=True)
        print(f"Output frames directory: {output_frames_path}")

    # Load first frame to get dimensions
    first_frame_path = classifications[0]['frame_path']
    first_frame = cv2.imread(first_frame_path)
    if first_frame is None:
        print(f"ERROR: Could not load first frame: {first_frame_path}")
        return

    frame_height, frame_width = first_frame.shape[:2]

    # Combined dimensions (frame + info panel side-by-side)
    combined_width = frame_width + panel_width
    combined_height = frame_height

    # Initialize video writer if needed
    video_writer = None
    if create_video:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_video, fourcc, fps,
                                       (combined_width, combined_height), isColor=True)
        print(f"Creating video: {output_video}")

    # Process each classification
    for idx, entry in enumerate(tqdm(classifications, desc="Creating visualization")):
        timepoint = entry['timepoint_minutes']
        frame_path = entry['frame_path']
        response = entry['response']

        # Parse classification
        classification = parse_classification_response(response)

        # Load frame
        frame = cv2.imread(frame_path)
        if frame is None:
            print(f"WARNING: Could not load frame: {frame_path}")
            continue

        # Create info panel
        info_panel = create_info_panel(panel_width, combined_height,
                                       timepoint, classification)

        # Combine frame and info panel side-by-side
        combined = np.hstack([frame, info_panel])

        # Add to video
        if video_writer:
            video_writer.write(combined)

        # Save frame
        if create_frames:
            output_path = output_frames_path / f"classified_frame_{idx:04d}.png"
            cv2.imwrite(str(output_path), combined)

    # Cleanup
    if video_writer:
        video_writer.release()
        print(f"Video saved: {output_video}")

    if create_frames:
        print(f"Frames saved to: {output_frames_dir}")

    # Create summary plot
    create_summary_plot(classifications, 'classification_summary.png')

    print("\nVisualization complete!")


def create_summary_plot(classifications, output_file='classification_summary.png'):
    """
    Create a summary plot showing stage progression over time.

    Parameters
    ----------
    classifications : list
        List of classification entries
    output_file : str
        Output image filename
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not installed, skipping summary plot")
        return

    # Parse all classifications
    timepoints = []
    stages = []
    confidences = []

    for entry in classifications:
        parsed = parse_classification_response(entry['response'])
        timepoints.append(entry['timepoint_minutes'])
        stages.append(parsed['stage'])
        confidences.append(parsed['confidence'])

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Plot 1: Stage over time
    ax1.scatter(timepoints, range(len(stages)), c=confidences,
                cmap='RdYlGn', s=100, vmin=0, vmax=1)
    ax1.set_yticks(range(len(stages)))
    ax1.set_yticklabels(stages)
    ax1.set_xlabel('Time (minutes)', fontsize=12)
    ax1.set_ylabel('Developmental Stage', fontsize=12)
    ax1.set_title('C. elegans Embryo Development (Claude VLM Classification)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax1)
    cbar.set_label('Confidence', fontsize=10)

    # Plot 2: Confidence over time
    ax2.plot(timepoints, confidences, 'o-', color='steelblue', linewidth=2, markersize=8)
    ax2.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='High confidence')
    ax2.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Medium confidence')
    ax2.set_xlabel('Time (minutes)', fontsize=12)
    ax2.set_ylabel('Classification Confidence', fontsize=12)
    ax2.set_ylim(0, 1.05)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Summary plot saved: {output_file}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Visualize Claude VLM embryo classification results'
    )
    parser.add_argument(
        '--classifications',
        default='embryo_classifications.json',
        help='JSON file with classifications (default: embryo_classifications.json)'
    )
    parser.add_argument(
        '--frames-dir',
        default='1_png',
        help='Directory with original frames (default: 1_png)'
    )
    parser.add_argument(
        '--output-video',
        default='embryo_classifications_annotated.mp4',
        help='Output video filename (default: embryo_classifications_annotated.mp4)'
    )
    parser.add_argument(
        '--output-frames',
        default='2_classified_png',
        help='Output directory for annotated frames (default: 2_classified_png)'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=2,
        help='Frames per second for video (default: 2)'
    )
    parser.add_argument(
        '--no-video',
        action='store_true',
        help='Skip video creation'
    )
    parser.add_argument(
        '--no-frames',
        action='store_true',
        help='Skip individual frame creation'
    )

    args = parser.parse_args()

    create_visualization(
        classifications_file=args.classifications,
        frames_dir=args.frames_dir,
        output_video=args.output_video,
        output_frames_dir=args.output_frames,
        fps=args.fps,
        create_video=not args.no_video,
        create_frames=not args.no_frames
    )
