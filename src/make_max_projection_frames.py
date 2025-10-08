#!/usr/bin/env python3
"""
Create individual PNG frames with max projection from C. elegans embryo time series.
Reads 3D TIFF stacks, creates max projections with annotations, and saves as PNG images.
"""

import numpy as np
from pathlib import Path
import tifffile
import cv2
from tqdm import tqdm
import pandas as pd

def create_max_projection_frames(
    embryo_dir='nih-ls/nih_diSPIM_deconv_1',
    output_dir='1_png',
    pixel_size_um=0.1625,
    scale_bar_um=10
):
    """
    Create max projection frames from 3D TIFF time series.

    Parameters:
    -----------
    embryo_dir : str
        Path to embryo directory containing 'images' folder
    output_dir : str
        Output directory for PNG frames
    pixel_size_um : float
        Pixel size in micrometers (default: 0.1625 um from README)
    scale_bar_um : float
        Scale bar length in micrometers (default: 10 um)
    """

    # Set up paths
    embryo_path = Path(embryo_dir)
    images_path = embryo_path / 'images'
    tracks_file = embryo_path / 'tracks' / 'tracks.txt'
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_path}")

    # Load tracks data
    print(f"Loading tracks from {tracks_file}")
    tracks_df = pd.read_csv(tracks_file, sep='\t')
    print(f"Loaded {len(tracks_df)} track points")

    # Calculate scale bar length in pixels
    scale_bar_pixels = int(scale_bar_um / pixel_size_um)

    # Get sorted list of TIFF files
    tiff_files = sorted(images_path.glob('*.tif'))
    print(f"Found {len(tiff_files)} time points")

    if len(tiff_files) == 0:
        print("No TIFF files found!")
        return

    # Read first image to get dimensions
    first_img = tifffile.imread(str(tiff_files[0]))
    print(f"Image shape: {first_img.shape}")

    # Create max projection for first frame to get 2D dimensions
    first_max_proj = np.max(first_img, axis=0)
    height, width = first_max_proj.shape

    print(f"Creating PNG frames...")

    # Process each time point
    for i, tiff_file in enumerate(tqdm(tiff_files, desc="Processing frames")):
        # Read 3D stack
        img_3d = tifffile.imread(str(tiff_file))

        # Create max projection along z-axis (axis 0)
        max_proj = np.max(img_3d, axis=0)

        # Convert to uint8 if needed
        if max_proj.dtype != np.uint8:
            max_proj = max_proj.astype(np.uint8)

        # Convert to color image for colored overlays
        frame_with_annotations = cv2.cvtColor(max_proj, cv2.COLOR_GRAY2BGR)

        # Get tracks for this time point
        tracks_at_t = tracks_df[tracks_df['t'] == i]

        # Draw nuclei positions
        for _, row in tracks_at_t.iterrows():
            x, y = int(row['x']), int(row['y'])
            radius = int(row['radius'])

            # Draw circle around nucleus
            cv2.circle(frame_with_annotations, (x, y), radius, (0, 255, 0), 1)
            # Draw center point
            cv2.circle(frame_with_annotations, (x, y), 2, (0, 255, 255), -1)

        # Add timestamp text
        timestamp_text = f"t={i:03d} ({i} min)"
        cv2.putText(
            frame_with_annotations,
            timestamp_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # Add cell count text
        num_cells = len(tracks_at_t)
        cell_count_text = f"Cells: {num_cells}"
        cv2.putText(
            frame_with_annotations,
            cell_count_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # Add scale bar in bottom right
        scale_bar_margin = 20
        scale_bar_thickness = 4
        scale_bar_x = width - scale_bar_pixels - scale_bar_margin
        scale_bar_y = height - scale_bar_margin

        # Draw scale bar
        cv2.line(
            frame_with_annotations,
            (scale_bar_x, scale_bar_y),
            (scale_bar_x + scale_bar_pixels, scale_bar_y),
            (255, 255, 255),
            scale_bar_thickness
        )

        # Add scale bar label
        scale_bar_text = f"{scale_bar_um} um"
        text_size = cv2.getTextSize(scale_bar_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = scale_bar_x + (scale_bar_pixels - text_size[0]) // 2
        text_y = scale_bar_y - 8
        cv2.putText(
            frame_with_annotations,
            scale_bar_text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Save frame as PNG
        output_filename = output_path / f"frame_{i:04d}.png"
        cv2.imwrite(str(output_filename), frame_with_annotations)

    print(f"Done! Saved {len(tiff_files)} frames to {output_path}")

if __name__ == '__main__':
    create_max_projection_frames()
