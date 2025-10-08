# C. elegans Embryo Classification with Claude VLM

This workflow uses Claude's vision capabilities to classify developmental stages of C. elegans embryos from time-lapse microscopy data.

## Overview

The pipeline consists of three main steps:

1. **Generate annotated frames** - Create max projection images with track overlays
2. **Sample frames** - Select frames at 10-minute intervals
3. **Classify with Claude** - Send frames to Claude API for developmental stage classification

## Dataset

- **Source**: Zenodo record 6460375 (NIH diSPIM C. elegans dataset)
- **Data**: 3 embryos with 3D time-lapse imaging + nucleus tracking
- **Temporal resolution**: 1 minute per frame
- **Frames**: 350-400 per embryo

## Scripts

### 1. `make_max_projection_video.py`
Creates an MP4 video with:
- Max projection of 3D stacks
- Nucleus tracking overlays (green circles)
- Cell count annotation
- Timestamp
- Scale bar

**Run**: `setup_and_run.bat`

### 2. `make_max_projection_frames.py`
Saves individual PNG frames to `1_png/` directory with same annotations as video.

**Run**: `python3 make_max_projection_frames.py`

### 3. `classify_embryo_stages.py`
Samples frames every 10 minutes and sends to Claude API for classification.

**Features**:
- Uses Claude Sonnet 4.5 vision model
- Samples every 10 minutes (configurable)
- Saves classifications to JSON
- Includes confidence scores and reasoning
- Budget-conscious: ~40 API calls for full 400-frame dataset

**Run**: `run_classification.bat`

### 4. `visualize_classifications.py`
Creates visualizations from the classification results JSON.

**Outputs**:
- Annotated video with side-by-side classification panel
- Individual annotated frames in `2_classified_png/`
- Summary plot showing stage progression and confidence over time

**Run**: `run_visualization.bat`

## Usage

### Step 1: Generate Frames

First, create the annotated PNG frames:

```bash
# Run the setup script (creates venv, installs deps, generates video)
setup_and_run.bat

# Then generate PNG frames
python3 make_max_projection_frames.py
```

This creates `1_png/frame_0000.png` through `1_png/frame_0399.png`.

### Step 2: Set API Key

Set your Anthropic API key as an environment variable:

```bash
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Run Classification

```bash
run_classification.bat
```

Or run directly with options:

```bash
python3 classify_embryo_stages.py --frames-dir 1_png --interval 10 --output results.json
```

**Arguments**:
- `--frames-dir`: Directory with PNG frames (default: `1_png`)
- `--interval`: Sample every N minutes (default: 10)
- `--output`: Output JSON file (default: `embryo_classifications.json`)
- `--api-key`: API key (or use ANTHROPIC_API_KEY env var)

### Step 4: Visualize Results

After classification completes, visualize the results:

```bash
run_visualization.bat
```

Or run directly with options:

```bash
python3 visualize_classifications.py --classifications embryo_classifications.json --fps 2
```

**Arguments**:
- `--classifications`: JSON file with classifications (default: `embryo_classifications.json`)
- `--frames-dir`: Directory with original frames (default: `1_png`)
- `--output-video`: Output video filename (default: `embryo_classifications_annotated.mp4`)
- `--output-frames`: Output frames directory (default: `2_classified_png`)
- `--fps`: Frames per second for video (default: 2)
- `--no-video`: Skip video creation
- `--no-frames`: Skip individual frame creation

## Output Format

The classification script produces a JSON file with this structure:

```json
[
  {
    "timepoint_minutes": 0,
    "frame_index": 0,
    "frame_path": "1_png\\frame_0000.png",
    "response": "**Developmental Stage**: 2-cell\n\n**Confidence**: 0.95\n\n**Reasoning**:...",
    "timestamp": "2025-10-07T14:30:00.000000"
  },
  ...
]
```

Each entry contains:
- **timepoint_minutes**: Time in minutes from start
- **frame_index**: Frame number in original sequence
- **frame_path**: Path to the analyzed image
- **response**: Claude's full classification response with:
  - Developmental stage
  - Confidence score (0-1)
  - Reasoning (visual features, cell count consistency, morphology)
  - Concerns/uncertainties
- **timestamp**: When classification was performed

## Cost Estimation

**Per frame**:
- Image tokens: ~1,500 tokens (after compression)
- Response: ~500 tokens
- Total: ~2,000 tokens per classification

**Full dataset (400 frames, sampling every 10 minutes)**:
- Frames analyzed: 40
- Total tokens: ~80,000 tokens
- Estimated cost: ~$0.30 (at current Claude Sonnet 4.5 pricing)

**Alternative sampling rates**:
- Every 5 minutes: 80 frames, ~$0.60
- Every 20 minutes: 20 frames, ~$0.15
- Every 30 minutes: 13 frames, ~$0.10

## Developmental Stages Expected

For a typical C. elegans embryo (350 minute timecourse):

| Time (min) | Expected Stage | Cell Count |
|------------|----------------|------------|
| 0          | 1-cell         | 1          |
| 10-20      | 2-4 cell       | 2-4        |
| 30-40      | ~14-cell       | 12-14      |
| 50-60      | ~24-cell       | 24-28      |
| 80-100     | ~90-cell       | 90         |
| 150-200    | ~190-350 cell  | 190-350    |
| 250+       | comma/elongation | 550+     |

## Dependencies

All installed via `setup_and_run.bat`:
- numpy
- tifffile
- opencv-python
- tqdm
- pandas
- anthropic
- pillow

## Visualization Outputs

The visualization script creates three types of outputs:

### 1. Annotated Video
Side-by-side layout showing:
- **Left**: Original frame with tracking annotations
- **Right**: Classification panel with:
  - Developmental stage
  - Confidence score (with color-coded bar)
  - Reasoning excerpt

### 2. Individual Annotated Frames
Saved to `2_classified_png/` for detailed inspection or creating custom visualizations.

### 3. Summary Plot
A matplotlib plot (`classification_summary.png`) showing:
- **Top panel**: Stage progression over time (colored by confidence)
- **Bottom panel**: Confidence scores over time

## Files Created

```
vlm_worm_test/
├── nih-ls/                                    # Downloaded Zenodo data
├── 1_png/                                     # Generated annotated frames
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── 2_classified_png/                          # Frames with classifications
│   ├── classified_frame_0000.png
│   ├── classified_frame_0001.png
│   └── ...
├── embryo1_max_projection.mp4                 # Original video output
├── embryo_classifications.json                # Classification results (JSON)
├── embryo_classifications_annotated.mp4       # Video with classifications
├── classification_summary.png                 # Summary plot
├── make_max_projection_video.py               # Video generation script
├── make_max_projection_frames.py              # Frame generation script
├── classify_embryo_stages.py                  # Classification script
├── visualize_classifications.py               # Visualization script
├── setup_and_run.bat                          # Setup + video generation
├── run_classification.bat                     # Run classification
└── run_visualization.bat                      # Create visualizations
```

## Notes

- The script saves results after each classification, so you can safely interrupt and resume
- Frame generation only needs to be done once
- You can re-run classification with different sampling intervals without regenerating frames
- Claude's responses include reasoning, which is valuable for understanding classification decisions
- Consider using a smaller interval (e.g., 5 min) during rapid development phases (first 100 minutes)
