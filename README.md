# C. elegans Embryo Classification with Claude VLM

Classify C. elegans embryo developmental stages using Claude's vision AI on time-lapse microscopy data.

## Quick Start

### 1. Download the Dataset

```bash
curl -C - -L -o nih_ls.zip "https://zenodo.org/api/records/6460375/files/nih_ls.zip/content"
unzip nih_ls.zip
```

**Dataset:** [Zenodo Record 6460375](https://zenodo.org/records/6460375) (27 GB)
- 3 C. elegans embryos with 3D time-lapse imaging
- Nucleus tracking data included
- 350-400 frames per embryo (1 min/frame)

### 2. Generate Annotated Frames

```bash
scripts\setup_and_run.bat  # Creates venv, installs deps, generates video
python3 src\make_max_projection_frames.py  # Generate PNG frames
```

### 3. Classify with Claude

Set your API key:
```bash
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Run classification:
```bash
# All 400 frames (~$3.60, ~2 min with concurrency)
scripts\run_classify_all_fast.bat

# Or sample every 10 minutes (~$0.30)
scripts\run_classification.bat
```

### 4. Visualize Results

```bash
python3 src\create_interactive_viewer.py --no-embed-images
scripts\serve_viewer_multi.bat
```

Open: http://localhost:8000/embryo_viewer_light.html

## Features

✅ **Concurrent Classification** - Process 10+ frames in parallel
✅ **Interactive Viewer** - Navigate classifications with arrows/slider
✅ **Timelapse Playback** - Auto-play through development
✅ **Confidence Scores** - See Claude's certainty for each stage
✅ **Detailed Reasoning** - View Claude's analysis and concerns
✅ **Prompt Inspector** - See exact prompts sent to Claude
✅ **Multi-user HTTP Server** - Share with team

## Python Scripts (src/)

| Script | Description |
|--------|-------------|
| `make_max_projection_video.py` | Create MP4 with tracking overlays |
| `make_max_projection_frames.py` | Generate individual PNG frames |
| `classify_embryo_stages.py` | Classify sampled frames (every N minutes) |
| `classify_all_frames.py` | Classify all frames sequentially |
| `classify_all_frames_concurrent.py` | Classify all frames in parallel (fast!) |
| `visualize_classifications.py` | Create annotated video from results |
| `create_interactive_viewer.py` | Generate HTML viewer |
| `serve_viewer_multithreaded.py` | HTTP server for viewer |

## Batch Scripts (scripts/)

| File | Purpose |
|------|---------|
| `setup_and_run.bat` | Setup + generate video |
| `run_classification.bat` | Sampled classification |
| `run_classify_all.bat` | Sequential full classification |
| `run_classify_all_fast.bat` | Concurrent full classification |
| `run_visualization.bat` | Generate annotated outputs |
| `create_viewer.bat` | Create HTML viewer |
| `serve_viewer_multi.bat` | Start HTTP server |

## Cost Estimates

| Frames | Interval | Cost | Time (concurrent) |
|--------|----------|------|-------------------|
| 40     | 10 min   | $0.30 | ~30 sec |
| 80     | 5 min    | $0.60 | ~1 min |
| 200    | 2 min    | $1.80 | ~2 min |
| 400    | All      | $3.60 | ~4 min |

## Project Structure

```
vlm_worm_test/
├── src/                             # Python source code
│   ├── make_max_projection_video.py
│   ├── make_max_projection_frames.py
│   ├── classify_embryo_stages.py
│   ├── classify_all_frames.py
│   ├── classify_all_frames_concurrent.py
│   ├── visualize_classifications.py
│   ├── create_interactive_viewer.py
│   └── serve_viewer_multithreaded.py
├── scripts/                         # Batch files for Windows
│   ├── setup_and_run.bat
│   ├── run_classification.bat
│   ├── run_classify_all.bat
│   ├── run_classify_all_fast.bat
│   ├── run_visualization.bat
│   ├── create_viewer.bat
│   ├── serve_viewer.bat
│   └── serve_viewer_multi.bat
├── docs/                            # Documentation
│   ├── QUICK_START.md
│   ├── README_CLASSIFICATION.md
│   └── PROMPTS.md
├── outputs/                         # Generated outputs
├── 1_png/                           # Generated annotated frames (400 PNGs)
├── 2_classified_png/                # Frames with classification info
├── embryo1_max_projection.mp4       # Basic annotated video
├── embryo_classifications_all.json  # Classification results
├── embryo_viewer_light.html         # Interactive viewer (2.2 MB)
├── classification_summary.png       # Timeline plot
├── nih-ls/                          # Downloaded dataset (27 GB)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Documentation

- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Quick reference guide
- **[docs/README_CLASSIFICATION.md](docs/README_CLASSIFICATION.md)** - Full documentation
- **[docs/PROMPTS.md](docs/PROMPTS.md)** - Exact prompts used

## Requirements

```
numpy
tifffile
opencv-python
tqdm
pandas
anthropic
pillow
matplotlib
```

Install with: `pip install -r requirements.txt`

## Dataset Citation

If you use this dataset, please cite:

> Moyle, M.W., Barnes, K.M., Kuchroo, M. et al. Structural and developmental principles of neuropil assembly in C. elegans. Nature 591, 99–104 (2021). https://doi.org/10.1038/s41586-020-03169-5

## License

MIT

## Credits

- **Dataset**: NIH-LS from Zenodo (Record 6460375)
- **Claude VLM**: Anthropic's Claude Sonnet 4.5
- **Analysis**: Automated developmental stage classification
