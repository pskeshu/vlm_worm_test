# Claude VLM Prompts for Embryo Classification

This document shows the exact prompts sent to Claude API.

## System Prompt

The following system prompt is sent with every API call to establish Claude's role and expertise:

```python
SYSTEM_PROMPT = """You are an expert developmental biologist specializing in C. elegans embryogenesis.

Your task is to classify embryo developmental stages from microscope images with nucleus tracking data.

You have deep knowledge of:
- C. elegans cell lineage and division patterns
- Characteristic morphological features at each developmental stage
- Expected cell counts at different time points
- Normal vs abnormal development

Be precise, analytical, and honest about uncertainty."""
```

This system prompt:
- Establishes domain expertise
- Sets expectations for the task
- Primes Claude with relevant knowledge areas
- Encourages calibrated confidence

## User Prompt

This is the actual prompt sent with each image (with variables filled in):

```
You are analyzing a time-lapse series of a developing C. elegans embryo.

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

Please be thorough in your reasoning and honest about uncertainties.
```

## Example Prompt for t=30 min with 12 cells

```
You are analyzing a time-lapse series of a developing C. elegans embryo.

This is a max projection image showing all nuclei (tracked cells shown with green circles).

**Time point**: 30 minutes into development
**Current cell count**: 12 cells

Please classify the developmental stage of this embryo and provide your reasoning.

[... rest of prompt same as above ...]
```

## Complete API Call

Both scripts (`classify_embryo_stages.py` and `classify_all_frames.py`) use this call:

```python
response = client.query(
    prompt=prompt,           # User prompt with timepoint/cell count
    system=SYSTEM_PROMPT,    # System prompt (developmental biologist)
    images=[image_rgb]       # The annotated frame
)
```

## Prompt Design Rationale

### Why This Structure?

1. **Context Setting**: Tells Claude this is a time-series analysis
2. **Visual Description**: Explains what the green circles mean
3. **Metadata**: Provides timepoint and cell count for reasoning
4. **Clear Categories**: Gives explicit stage definitions
5. **Structured Output**: Requests specific format for parsing
6. **Encourages Uncertainty**: Explicitly asks for confidence and concerns

### What Makes It Effective?

- **Multimodal Integration**: Combines visual + temporal + quantitative data
- **Domain Expertise**: Uses correct C. elegans terminology
- **Reasoning Encouragement**: Asks "why" not just "what"
- **Calibrated Confidence**: Explicitly requests uncertainty estimation
- **Parseable Format**: Markdown structure enables automated parsing

## Cost Per Image

With this prompt:
- User prompt: ~400 tokens
- Image: ~1,500 tokens (compressed)
- Response: ~500 tokens
- **Total per image: ~2,400 tokens**

For all 400 frames:
- Total tokens: ~960,000 tokens
- Estimated cost: **~$3.60** (at Claude Sonnet 4.5 rates)

Still very affordable for a complete developmental time-series analysis!
