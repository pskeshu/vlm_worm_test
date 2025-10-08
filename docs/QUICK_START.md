# Quick Start Guide - Embryo Classification with Claude

## Overview

Classify C. elegans embryo developmental stages using Claude's vision AI.

## Complete Workflow

### 1. Generate Annotated Frames (One Time)

```bash
# Creates venv, installs dependencies, generates video
setup_and_run.bat

# Generate individual PNG frames with annotations
python3 make_max_projection_frames.py
```

**Output**: `1_png/` folder with 400 annotated frames

---

### 2. Set API Key

```bash
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

### 3. Run Classification

**Option A: Sample Every 10 Minutes (~$0.30)**

```bash
run_classification.bat
```

**Option B: Classify ALL Frames (~$3.60)**

```bash
run_classify_all.bat
```

**Output**: JSON file with classifications, confidence, reasoning

---

### 4. Visualize Results

```bash
run_visualization.bat
```

**Outputs**:
- `embryo_classifications_annotated.mp4` - Side-by-side video
- `2_classified_png/` - Individual annotated frames
- `classification_summary.png` - Timeline plot

---

## Prompts Used

See `PROMPTS.md` for the exact prompts sent to Claude.

**User Prompt** (per frame):
- Context: Time-lapse analysis
- Metadata: Timepoint (min) + cell count
- Task: Classify developmental stage
- Output: Stage, confidence, reasoning

**System Prompt**: None (can be added if desired)

---

## Key Features

✅ **Actual cell counts** from tracking data (not estimated)
✅ **Resume capability** - Can interrupt and continue
✅ **Progress saving** - Results saved after each frame
✅ **Cost estimation** - Shows cost before running
✅ **Detailed reasoning** - Claude explains its classification
✅ **Confidence scores** - Quantified uncertainty

---

## Cost Summary

| Frames | Interval | Approx Cost |
|--------|----------|-------------|
| 40     | 10 min   | $0.30       |
| 80     | 5 min    | $0.60       |
| 200    | 2 min    | $1.80       |
| 400    | All      | $3.60       |

---

## Files

```
vlm_worm_test/
├── setup_and_run.bat              # Setup + generate video
├── run_classification.bat         # Classify sampled frames
├── run_classify_all.bat           # Classify ALL frames
├── run_visualization.bat          # Visualize results
│
├── classify_embryo_stages.py      # Sampled classification
├── classify_all_frames.py         # Full classification
├── visualize_classifications.py   # Create visualizations
│
├── PROMPTS.md                     # Exact prompts used
├── README_CLASSIFICATION.md       # Full documentation
└── QUICK_START.md                 # This file
```

---

## Tips

- Run sampled classification first to test the workflow
- Use `classify_all_frames.py` for publication-quality data
- The visualization script works with either JSON output
- You can re-run visualization without re-classifying

---

## Example Commands

```bash
# Classify all frames with custom output
python3 classify_all_frames.py --output my_results.json

# Visualize with custom settings
python3 visualize_classifications.py --classifications my_results.json --fps 5

# Sample every 20 minutes (lower cost)
python3 classify_embryo_stages.py --interval 20 --output sparse_results.json
```
