# VLM Benchmarking Framework - Design Plan

## Overview

This document outlines a comprehensive benchmarking framework for systematically evaluating Vision Language Model (VLM) performance on C. elegans embryo classification tasks.

## Current State Analysis

### What We're Testing
- C. elegans embryo developmental stage classification using Claude VLM
- Single timepoint classification (no temporal context between frames)
- Each query is independent - no conversation or context from previous timepoints

### Variables Currently Being Experimented With
- System and user prompts
- Cell count information (from tracking data)
- Timepoint information (minutes into development)
- Track annotations (green circles on nuclei)
- Classification granularity (1-cell, 2-cell, 4-cell, ~14-cell, ~90-cell, comma, 1.5-fold, etc.)

### Current Gaps
- No systematic configuration management
- No evaluation metrics or ground truth comparison
- No automated report generation
- No A/B testing framework for prompts
- No consistency testing (same image, different runs)
- No temporal context experiments (adding previous frame info)

## Proposed Benchmarking Framework

### Architecture Overview

```
benchmarking/
├── config/
│   ├── benchmark_config.py          # Experiment configuration classes
│   ├── prompt_templates.py          # Prompt variation library
│   └── experiment_presets.py        # Pre-defined experiment sets
├── runner/
│   ├── benchmark_runner.py          # Main experiment orchestrator
│   └── experiment_tracker.py        # Track progress, resume support
├── evaluation/
│   ├── metrics.py                   # Calculate all metrics
│   ├── ground_truth.py              # Ground truth management
│   └── consistency_checker.py       # Test-retest reliability
├── reporting/
│   ├── report_generator.py          # Generate HTML/JSON reports
│   ├── visualizations.py            # Plots and charts
│   └── statistical_analysis.py      # Significance testing
├── utils/
│   ├── annotation_tool.py           # Simple ground truth labeling
│   └── result_parser.py             # Parse Claude responses
└── examples/
    ├── run_prompt_comparison.py     # Example: Compare 3 prompts
    ├── run_context_ablation.py      # Example: Test ±context features
    └── run_temporal_experiment.py   # Example: Add temporal context
```

---

## Component Details

### 1. Experiment Configuration System

**Purpose**: Define all testable dimensions in a structured, reproducible way

**Configuration Dimensions**:

#### A. Prompt Variations
- **System prompt variants**:
  - Baseline (current "expert developmental biologist")
  - Minimal ("You are an AI assistant")
  - Verbose (detailed C. elegans lifecycle info)
  - Chain-of-thought oriented

- **User prompt variants**:
  - Current structured prompt
  - Minimal (just image + "classify stage")
  - Question format ("What stage is this embryo?")
  - Few-shot examples included

- **Classification granularity**:
  - Coarse (early, mid, late)
  - Medium (current 13 categories)
  - Fine (cell-count specific: 1, 2, 3, 4, 5, 6, 7, 8...)

#### B. Context Variations
- **Metadata inclusion** (factorial design):
  - ✓/✗ Cell count
  - ✓/✗ Timepoint (minutes)
  - ✓/✗ Expected stage for timepoint
  - ✓/✗ Track radius information
  - ✓/✗ Previous timepoint classification

- **Visual variations**:
  - With/without track annotations (green circles)
  - Raw grayscale vs annotated color
  - Different annotation styles (circles, dots, masks)
  - Cropped vs full frame

#### C. Temporal Context Experiments
- **No context** (current): Each frame classified independently
- **Previous N frames**: Include previous 1, 2, 3 frames in context
- **Conversation mode**: Build conversation history with all previous classifications
- **Sliding window**: Include previous + next frame (for non-real-time analysis)
- **Full trajectory**: Show cell count trajectory plot alongside image

#### D. Model Parameters
- **Temperature**: 0.0, 0.5, 1.0
- **Max tokens**: 512, 1024, 2048
- **Model versions**: Different Claude models if available

#### E. Sampling Strategies
- **All frames** (400 frames)
- **Every N minutes** (1, 2, 5, 10 min intervals)
- **Stage-based sampling** (more samples during transitions)
- **Uncertainty-based sampling** (resample low-confidence predictions)

**Implementation**: YAML configuration files

```yaml
experiment:
  name: "prompt_comparison_baseline_vs_minimal"
  description: "Compare current prompt vs minimal prompt"

  configurations:
    - name: "baseline"
      system_prompt: "expert_biologist"
      user_prompt: "structured_detailed"
      include_cell_count: true
      include_timepoint: true
      temperature: 1.0

    - name: "minimal"
      system_prompt: "minimal"
      user_prompt: "simple_question"
      include_cell_count: false
      include_timepoint: false
      temperature: 1.0

  dataset:
    frames_dir: "1_png"
    sample_strategy: "every_10min"

  evaluation:
    metrics: ["accuracy", "consistency", "confidence_calibration"]
    n_repeats: 3  # For consistency testing
```

---

### 2. Automated Benchmark Runner

**Purpose**: Execute experiments systematically with resume capability

**Features**:
- **Parallel execution**: Run multiple configurations concurrently
- **Resume support**: Continue from interruptions
- **Cost estimation**: Calculate $ before running
- **Progress tracking**: Real-time updates, ETA
- **Caching**: Avoid re-classifying same (image, prompt) pairs
- **Factorial experiment support**: Auto-generate all combinations

**Key Functions**:
```python
class BenchmarkRunner:
    def run_experiment(config_path: str, dry_run: bool = False)
    def run_factorial_experiment(factors: Dict, dataset: str)
    def estimate_cost(config: ExperimentConfig) -> float
    def resume_experiment(experiment_id: str)
```

**Output Format**:
```json
{
  "experiment_id": "20251009_prompt_comparison_001",
  "config": {...},
  "results": [
    {
      "configuration": "baseline",
      "frame_index": 0,
      "timepoint": 0,
      "predicted_stage": "2-cell",
      "confidence": 0.95,
      "reasoning": "...",
      "raw_response": "...",
      "cost": 0.009,
      "latency_ms": 1234
    },
    ...
  ]
}
```

---

### 3. Evaluation & Metrics Module

**Purpose**: Quantify VLM performance across multiple dimensions

#### A. Accuracy Metrics (requires ground truth)
- **Exact match accuracy**: % exactly correct
- **Off-by-one accuracy**: % within one stage
- **Stage-group accuracy**: Coarse grouping (early/mid/late)
- **Confusion matrix**: Which stages are confused?
- **Per-stage F1 scores**: Performance on each stage

#### B. Consistency Metrics
- **Test-retest reliability**: Run same config 3x, measure agreement
  - Cohen's kappa
  - Krippendorff's alpha
- **Configuration agreement**: Compare different configs on same images
- **Temperature sensitivity**: How much does temperature affect output?

#### C. Confidence Calibration
- **Calibration curve**: Are 90% confident predictions 90% accurate?
- **Expected Calibration Error (ECE)**
- **Brier score**
- **Overconfidence/underconfidence analysis**

#### D. Response Quality Metrics
- **Reasoning length**: Tokens in reasoning section
- **Uncertainty acknowledgment**: Does it mention concerns?
- **Feature citation**: Does it reference cell count, morphology, etc.?
- **Hallucination detection**: Claims not supported by image

#### E. Operational Metrics
- **Cost per classification**
- **Latency (ms per classification)**
- **Tokens used (input/output)**
- **API error rate**

#### F. Temporal Consistency
- **Stage progression validity**: Does stage sequence make biological sense?
- **Jump detection**: Identify non-monotonic progressions (4-cell → 2-cell → 8-cell)
- **Smoothness score**: Penalize erratic stage changes

**Implementation**:
```python
class MetricsCalculator:
    def calculate_accuracy(predictions, ground_truth)
    def calculate_consistency(run1, run2, run3)
    def calculate_confidence_calibration(predictions, ground_truth)
    def calculate_temporal_consistency(predictions_timeseries)
    def generate_confusion_matrix(predictions, ground_truth)
```

---

### 4. Report Generator

**Purpose**: Create comprehensive, publication-quality reports

#### A. Report Types

**1. Single Configuration Report**
- Classification timeline (predicted stages over time)
- Confidence plot
- Sample predictions (low/mid/high confidence)
- Stage distribution histogram
- Cost summary

**2. Comparison Report** (2+ configurations)
- Side-by-side accuracy comparison table
- Statistical significance tests (McNemar's test, paired t-test)
- Agreement heatmap (configuration pairs)
- Cost-benefit analysis
- Disagreement case analysis (frames where configs differ)

**3. Ablation Report** (context features)
- Marginal contribution of each feature
- Interaction effects
- Optimal feature subset

**4. Temporal Context Report**
- Does adding previous frames help?
- Conversation mode vs independent
- Temporal consistency improvement

#### B. Visualizations

**Essential Plots**:
- **Timeline plot**: Stage progression over time (color-coded by confidence)
- **Confusion matrix**: Ground truth vs predicted
- **Calibration curve**: Confidence vs accuracy
- **Cost vs performance**: Pareto frontier
- **Agreement matrix**: Inter-configuration agreement
- **Error distribution**: By stage, timepoint, cell count
- **Confidence distribution**: Histogram with accuracy overlay

**Interactive HTML Dashboard**:
- Navigate through frames
- Click to see predictions from all configurations
- Filter by stage, confidence, agreement
- View raw responses and reasoning
- Compare predictions side-by-side

**Implementation**:
```python
class ReportGenerator:
    def generate_html_report(experiment_results, output_path)
    def generate_comparison_report(experiments: List, output_path)
    def create_interactive_dashboard(experiments: List, output_path)
    def export_latex_tables(results)  # For papers
```

---

### 5. Ground Truth Support

**Purpose**: Enable accuracy evaluation through manual annotation

#### A. Ground Truth Sources
- **Manual annotation**: Simple labeling tool
- **Import existing labels**: From CSV/JSON
- **Consensus labels**: Combine multiple annotators
- **Semi-automated**: Use high-confidence VLM predictions as starting point

#### B. Annotation Tool Features
- Web-based interface (Flask/Streamlit)
- Navigate through frames with keyboard
- Dropdown for stage selection
- Confidence rating (low/medium/high)
- Notes field for ambiguous cases
- Progress tracking
- Export to JSON/CSV

#### C. Inter-Annotator Agreement
- Calculate agreement between annotators
- Identify controversial frames
- Generate consensus labels (majority vote, weighted by confidence)

**Implementation**:
```python
class GroundTruthManager:
    def load_ground_truth(path: str) -> Dict
    def calculate_inter_annotator_agreement(annotators: List)
    def generate_consensus_labels(annotators: List, method: str)
    def export_ground_truth(labels: Dict, format: str)
```

**Annotation Tool** (Streamlit app):
```python
# streamlit run utils/annotation_tool.py
# Navigate frames, select stage, save progress
```

---

### 6. Temporal Context Experiments

**Purpose**: Test if adding temporal context improves classification

#### A. Experiment Types

**1. Previous Frame Context**
```
User prompt includes:
"Previous frame (t=N-1): classified as 2-cell with confidence 0.95"
Current frame (t=N): [image to classify]
```

**2. Conversation Mode**
Build ongoing conversation:
```
System: Classify this embryo
Assistant: This is 2-cell stage
System: [next image] What stage is this now?
Assistant: This is 4-cell stage
System: [next image] What stage is this now?
```

**3. Trajectory Context**
Include cell count trajectory:
```
Cell count history:
t=0: 2 cells
t=1: 2 cells
t=2: 2 cells
t=3: 3 cells (you are here)

Current image at t=3: [image]
```

**4. Multi-frame Visual Context**
Send previous N frames as separate images:
```
content: [
  {"type": "image", "source": frame_t-2},
  {"type": "image", "source": frame_t-1},
  {"type": "image", "source": frame_t},
  {"type": "text", "text": "These are 3 consecutive frames..."}
]
```

#### B. Evaluation Questions
- Does temporal context improve accuracy?
- Does it improve consistency (reduce jumps)?
- Does it increase confidence?
- What's the optimal amount of context?
- Does it increase cost significantly?
- Does conversation mode drift over time?

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] `config/benchmark_config.py` - Configuration classes
- [ ] `config/prompt_templates.py` - Prompt library
- [ ] `runner/benchmark_runner.py` - Basic runner
- [ ] `utils/result_parser.py` - Parse VLM responses

### Phase 2: Metrics & Evaluation (Week 2)
- [ ] `evaluation/metrics.py` - All metrics
- [ ] `evaluation/consistency_checker.py` - Test-retest
- [ ] Ground truth format specification
- [ ] Basic report generation

### Phase 3: Reporting & Visualization (Week 3)
- [ ] `reporting/visualizations.py` - Core plots
- [ ] `reporting/report_generator.py` - HTML reports
- [ ] Interactive dashboard prototype
- [ ] Statistical comparison functions

### Phase 4: Ground Truth & Annotation (Week 4)
- [ ] `utils/annotation_tool.py` - Simple web UI
- [ ] `evaluation/ground_truth.py` - GT management
- [ ] Inter-annotator agreement calculation
- [ ] Sample dataset annotation (~50 frames)

### Phase 5: Temporal Experiments (Week 5)
- [ ] Temporal context prompt variants
- [ ] Conversation mode implementation
- [ ] Multi-frame visual context
- [ ] Temporal consistency metrics
- [ ] Comparative evaluation

### Phase 6: Examples & Documentation (Week 6)
- [ ] `examples/run_prompt_comparison.py`
- [ ] `examples/run_context_ablation.py`
- [ ] `examples/run_temporal_experiment.py`
- [ ] Full documentation and tutorial
- [ ] Sample experiment gallery

---

## Example Experiments

### Experiment 1: Prompt Engineering Comparison
**Question**: Which prompt style works best?

**Configurations**:
- Baseline (current)
- Minimal
- Chain-of-thought
- Few-shot (with examples)

**Dataset**: 40 frames (every 10 min)

**Metrics**: Accuracy, consistency (3 runs), cost

**Expected output**: Comparison report showing which prompt achieves best accuracy-cost tradeoff

---

### Experiment 2: Context Ablation Study
**Question**: Which context features matter most?

**Factorial design** (2^3 = 8 configurations):
- Cell count: ✓/✗
- Timepoint: ✓/✗
- Track annotations: ✓/✗

**Dataset**: 40 frames

**Metrics**: Accuracy, feature importance

**Expected output**: Ranking of features by contribution to accuracy

---

### Experiment 3: Temporal Context Impact
**Question**: Does adding previous frame context help?

**Configurations**:
- No context (baseline)
- Previous 1 frame
- Previous 2 frames
- Conversation mode

**Dataset**: Full 400 frames

**Metrics**: Accuracy, temporal consistency, stage jump frequency

**Expected output**: Report showing if temporal context reduces classification errors and improves biological plausibility

---

### Experiment 4: Classification Granularity
**Question**: Does finer granularity hurt performance?

**Configurations**:
- Coarse (3 stages: early/mid/late)
- Medium (13 stages: current)
- Fine (exact cell count: 1, 2, 3, 4...)

**Dataset**: 40 frames

**Metrics**: Accuracy, confidence, agreement

**Expected output**: Analysis of optimal granularity level

---

### Experiment 5: Temperature Sensitivity
**Question**: How does temperature affect outputs?

**Configurations**:
- Temperature: 0.0, 0.3, 0.5, 0.7, 1.0

**Dataset**: 40 frames, 3 repeats each

**Metrics**: Consistency, confidence variation

**Expected output**: Recommendation for optimal temperature

---

## Key Features Summary

1. **YAML-based experiment configs** for easy customization
2. **Automated factorial experiments** (test all combinations)
3. **Ground truth annotation tool** for manual labeling
4. **Statistical comparison** with significance tests
5. **Interactive HTML reports** with drill-down capabilities
6. **Temporal context testing** (your mentioned next step)
7. **Cost-optimized sampling** for expensive experiments
8. **Resume capability** for long-running experiments
9. **Confidence calibration analysis**
10. **Publication-ready visualizations** and tables

---

## Expected Outcomes

After implementing this framework, you will be able to:

1. **Systematically compare** prompt variations and identify the best performing prompt
2. **Quantify** the value of each context feature (cell count, timepoint, etc.)
3. **Measure** test-retest reliability and determine if outputs are stable
4. **Evaluate** if temporal context improves classification accuracy
5. **Optimize** cost vs performance tradeoff
6. **Generate** publication-quality reports automatically
7. **Build** a ground truth dataset for ongoing evaluation
8. **Track** performance over time as models improve
9. **Share** results with collaborators via interactive dashboards
10. **Make data-driven decisions** about prompt engineering and model configuration

---

## Cost Estimates

Assuming Claude Sonnet 4.5 at ~$3.60 per 400 frames:

- **Single experiment** (40 frames): ~$0.36
- **Prompt comparison** (4 prompts × 40 frames): ~$1.44
- **Factorial ablation** (8 configs × 40 frames): ~$2.88
- **Consistency testing** (3 runs × 40 frames): ~$1.08
- **Temporal experiment** (4 configs × 400 frames): ~$14.40

**Total for all example experiments**: ~$20

This framework enables comprehensive benchmarking at reasonable cost.

---

## Next Steps

1. **Review this plan** - Does it address your benchmarking needs?
2. **Prioritize components** - Which modules are most important to you?
3. **Create ground truth** - Annotate ~50 frames manually for evaluation
4. **Start with Phase 1** - Build core infrastructure
5. **Run first experiment** - Prompt comparison baseline
6. **Iterate** - Refine based on initial results

---

## Questions to Consider

1. Do you have existing ground truth annotations, or do we need to create them?
2. Which experimental questions are highest priority?
3. What's your budget/timeline for benchmarking?
4. Do you want to test multiple embryos (you have 3 in the dataset)?
5. Should we include experiments with different model providers (GPT-4V, Gemini)?
6. Do you want real-time classification capability, or offline analysis only?

---

## References & Related Work

- **VLM Benchmarking**: Papers on evaluating vision-language models
- **Confidence Calibration**: Expected Calibration Error (ECE), calibration curves
- **Inter-Annotator Agreement**: Cohen's kappa, Krippendorff's alpha
- **Temporal Consistency**: Metrics for sequential predictions
- **A/B Testing**: Statistical methods for comparing configurations

This framework draws inspiration from:
- ML experiment tracking tools (MLflow, Weights & Biases)
- Medical image analysis benchmarks (MICCAI challenges)
- Prompt engineering frameworks (LangChain, PromptTools)
