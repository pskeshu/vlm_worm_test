#!/usr/bin/env python3
"""
Create an interactive HTML viewer for embryo classification results.
Displays images with parsed classifications and navigation controls.
"""

import json
import re
import base64
from pathlib import Path


def parse_classification_response(response_text):
    """
    Parse Claude's response to extract structured data.
    Handles both markdown (#) and bold (**) formats.

    Returns
    -------
    dict
        Parsed classification with keys: stage, confidence, reasoning, concerns
    """
    result = {
        'stage': 'Unknown',
        'confidence': 0.0,
        'reasoning': '',
        'concerns': ''
    }

    # Extract stage - try multiple patterns
    # Pattern 1: ## 1. Developmental Stage: **2-cell**
    stage_match = re.search(r'##\s*1\.\s*Developmental Stage:?\s*\*\*(.+?)\*\*', response_text, re.IGNORECASE)
    if not stage_match:
        # Pattern 2: **Developmental Stage**: something
        stage_match = re.search(r'\*\*Developmental Stage\*\*:?\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE)
    if stage_match:
        result['stage'] = stage_match.group(1).strip()

    # Extract confidence - try multiple patterns
    # Pattern 1: ## 2. Confidence: **0.95**
    conf_match = re.search(r'##\s*2\.\s*Confidence:?\s*\*\*([0-9.]+)\*\*', response_text, re.IGNORECASE)
    if not conf_match:
        # Pattern 2: **Confidence**: 0.95
        conf_match = re.search(r'\*\*Confidence\*\*:?\s*([0-9.]+)', response_text, re.IGNORECASE)
    if conf_match:
        result['confidence'] = float(conf_match.group(1))

    # Extract reasoning section
    # Pattern 1: ## 3. Reasoning: ... ## 4.
    reasoning_match = re.search(
        r'##\s*3\.\s*Reasoning:?\s*\n(.+?)(?:\n##\s*4\.|$)',
        response_text,
        re.IGNORECASE | re.DOTALL
    )
    if not reasoning_match:
        # Pattern 2: **Reasoning**: ... **Concerns
        reasoning_match = re.search(
            r'\*\*Reasoning\*\*:?\s*\n(.+?)(?:\n\*\*|$)',
            response_text,
            re.IGNORECASE | re.DOTALL
        )
    if reasoning_match:
        result['reasoning'] = reasoning_match.group(1).strip()

    # Extract concerns section
    # Pattern 1: ## 4. Concerns or Uncertainties: ...
    concerns_match = re.search(
        r'##\s*4\.\s*Concerns or Uncertainties:?\s*\n(.+?)$',
        response_text,
        re.IGNORECASE | re.DOTALL
    )
    if not concerns_match:
        # Pattern 2: **Concerns or Uncertainties**: ...
        concerns_match = re.search(
            r'\*\*Concerns or Uncertainties\*\*:?\s*\n(.+?)(?:\n\*\*|$)',
            response_text,
            re.IGNORECASE | re.DOTALL
        )
    if concerns_match:
        result['concerns'] = concerns_match.group(1).strip()

    return result


def image_to_base64(image_path):
    """Convert image to base64 for embedding in HTML."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def create_html_viewer(
    classifications_file='embryo_classifications_all.json',
    output_file='embryo_viewer.html',
    include_images=True
):
    """
    Create interactive HTML viewer for classification results.

    Parameters
    ----------
    classifications_file : str
        Path to JSON file with classifications
    output_file : str
        Output HTML filename
    include_images : bool
        Whether to embed images (makes HTML large but standalone)
    """

    print(f"Loading classifications from {classifications_file}...")
    with open(classifications_file, 'r') as f:
        classifications = json.load(f)

    print(f"Found {len(classifications)} classifications")

    # Parse all classifications
    print("Parsing classifications...")
    parsed_data = []
    for entry in classifications:
        parsed = parse_classification_response(entry['response'])
        # Convert Windows backslashes to forward slashes for web compatibility
        frame_path = entry['frame_path'].replace('\\', '/')
        parsed_data.append({
            'frame_index': entry['frame_index'],
            'timepoint': entry['timepoint_minutes'],
            'cell_count': entry['cell_count'],
            'frame_path': frame_path,
            'stage': parsed['stage'],
            'confidence': parsed['confidence'],
            'reasoning': parsed['reasoning'],
            'concerns': parsed['concerns'],
            'raw_response': entry['response']
        })

    # Sort by frame index
    parsed_data.sort(key=lambda x: x['frame_index'])

    # Encode images if requested
    if include_images:
        print("Encoding images (this may take a moment)...")
        for i, data in enumerate(parsed_data):
            if i % 50 == 0:
                print(f"  {i}/{len(parsed_data)}")
            try:
                data['image_b64'] = image_to_base64(data['frame_path'])
            except Exception as e:
                print(f"Warning: Could not load {data['frame_path']}: {e}")
                data['image_b64'] = None

    # Create HTML
    print("Generating HTML...")
    html = create_html_content(parsed_data, include_images)

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✓ Created interactive viewer: {output_file}")
    print(f"  Open in your browser to view results!")
    if include_images:
        print(f"  Note: File is large (~{len(html)/1024/1024:.1f} MB) because images are embedded")


def create_html_content(parsed_data, include_images):
    """Generate HTML content."""

    # Convert data to JSON for embedding
    data_json = json.dumps(parsed_data, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C. elegans Embryo Development Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            color: white;
        }}

        .header p {{
            font-size: 1.1rem;
            color: rgba(255,255,255,0.9);
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .controls {{
            background: #2a2a2a;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}

        .control-group {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}

        .control-group label {{
            font-weight: 600;
            color: #b0b0b0;
        }}

        button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.2s;
        }}

        button:hover {{
            background: #5568d3;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }}

        button:disabled {{
            background: #4a4a4a;
            cursor: not-allowed;
            transform: none;
        }}

        input[type="range"] {{
            flex: 1;
            min-width: 200px;
        }}

        input[type="number"] {{
            background: #1a1a1a;
            border: 1px solid #444;
            color: #e0e0e0;
            padding: 0.5rem;
            border-radius: 4px;
            width: 80px;
        }}

        .content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        @media (max-width: 1200px) {{
            .content {{
                grid-template-columns: 1fr;
            }}
        }}

        .image-panel {{
            background: #2a2a2a;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .image-panel img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }}

        .info-panel {{
            background: #2a2a2a;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .info-section {{
            margin-bottom: 1.5rem;
        }}

        .info-section h2 {{
            color: #667eea;
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .metadata-item {{
            background: #1a1a1a;
            padding: 1rem;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}

        .metadata-item .label {{
            font-size: 0.85rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .metadata-item .value {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #e0e0e0;
            margin-top: 0.25rem;
        }}

        .stage-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .confidence-bar {{
            width: 100%;
            height: 30px;
            background: #1a1a1a;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
            margin-top: 0.5rem;
        }}

        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
        }}

        .confidence-fill.high {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        }}

        .confidence-fill.medium {{
            background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        }}

        .confidence-fill.low {{
            background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
        }}

        .text-content {{
            background: #1a1a1a;
            padding: 1rem;
            border-radius: 8px;
            line-height: 1.8;
            color: #c0c0c0;
        }}

        .text-content p {{
            margin-bottom: 0.5rem;
        }}

        .summary {{
            background: #2a2a2a;
            padding: 1.5rem;
            border-radius: 12px;
            margin-top: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .summary h2 {{
            color: #667eea;
            margin-bottom: 1rem;
        }}

        .timeline {{
            margin-top: 2rem;
            padding: 1rem;
            background: #1a1a1a;
            border-radius: 8px;
        }}

        .keyboard-hint {{
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-top: 1rem;
        }}

        .raw-response {{
            background: #1a1a1a;
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
            color: #a0a0a0;
        }}

        .toggle-raw {{
            background: #3a3a3a;
            color: #888;
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 C. elegans Embryo Development Viewer</h1>
        <p>Claude VLM Classification Results - 400 Time Points</p>
    </div>

    <div class="container">
        <div class="controls">
            <div class="control-group">
                <button id="prevBtn" onclick="previousFrame()">← Previous</button>
                <button id="nextBtn" onclick="nextFrame()">Next →</button>
            </div>

            <div class="control-group">
                <label for="frameSlider">Frame:</label>
                <input type="range" id="frameSlider" min="0" max="399" value="0"
                       oninput="goToFrame(parseInt(this.value))">
                <input type="number" id="frameInput" min="0" max="399" value="0"
                       onchange="goToFrame(parseInt(this.value))">
                <span id="frameLabel">0 / 399</span>
            </div>

            <div class="control-group">
                <button onclick="goToFrame(0)">⏮ First</button>
                <button onclick="goToFrame(data.length - 1)">Last ⏭</button>
            </div>

            <div class="control-group">
                <button onclick="playTimelapse()">▶ Play</button>
                <button onclick="stopTimelapse()">⏸ Pause</button>
            </div>
        </div>

        <div class="content">
            <div class="image-panel">
                <img id="frameImage" src="" alt="Embryo frame">
            </div>

            <div class="info-panel">
                <div class="metadata">
                    <div class="metadata-item">
                        <div class="label">Time</div>
                        <div class="value" id="timepoint">0 min</div>
                    </div>
                    <div class="metadata-item">
                        <div class="label">Cell Count</div>
                        <div class="value" id="cellCount">-</div>
                    </div>
                    <div class="metadata-item">
                        <div class="label">Frame</div>
                        <div class="value" id="frameNum">0</div>
                    </div>
                </div>

                <div class="info-section">
                    <h2>Classification</h2>
                    <div class="stage-badge" id="stage">-</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" id="confidenceFill">
                            <span id="confidenceText">0%</span>
                        </div>
                    </div>
                </div>

                <div class="info-section">
                    <h2>Reasoning</h2>
                    <div class="text-content" id="reasoning">-</div>
                </div>

                <div class="info-section" id="concernsSection">
                    <h2>Concerns / Uncertainties</h2>
                    <div class="text-content" id="concerns">-</div>
                </div>

                <button class="toggle-raw" onclick="toggleRawResponse()">
                    Show Raw Response
                </button>
                <div class="raw-response" id="rawResponse" style="display: none;"></div>

                <button class="toggle-raw" onclick="togglePrompts()">
                    Show System & User Prompts
                </button>
                <div class="raw-response" id="prompts" style="display: none;"></div>
            </div>
        </div>

        <div class="keyboard-hint">
            💡 Tip: Use arrow keys ← → to navigate frames
        </div>
    </div>

    <script>
        // System and User Prompts
        const SYSTEM_PROMPT = `You are an expert developmental biologist specializing in C. elegans embryogenesis.

Your task is to classify embryo developmental stages from microscope images with nucleus tracking data.

You have deep knowledge of:
- C. elegans cell lineage and division patterns
- Characteristic morphological features at each developmental stage
- Expected cell counts at different time points
- Normal vs abnormal development

Be precise, analytical, and honest about uncertainty.`;

        const USER_PROMPT_TEMPLATE = `You are analyzing a time-lapse series of a developing C. elegans embryo.

This is a max projection image showing all nuclei (tracked cells shown with green circles).

**Time point**: {{timepoint}} minutes into development
**Tracked cell count**: {{cell_count}} cells

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

Please be thorough in your reasoning and honest about uncertainties.`;

        // Embedded data
        const data = {data_json};

        let currentIndex = 0;
        let timelapseInterval = null;

        function updateDisplay() {{
            const frame = data[currentIndex];

            // Update image
            {"document.getElementById('frameImage').src = 'data:image/png;base64,' + frame.image_b64;" if include_images else "document.getElementById('frameImage').src = frame.frame_path;"}

            // Update metadata
            document.getElementById('timepoint').textContent = frame.timepoint + ' min';
            document.getElementById('cellCount').textContent = frame.cell_count;
            document.getElementById('frameNum').textContent = frame.frame_index;

            // Update classification
            document.getElementById('stage').textContent = frame.stage;

            // Update confidence
            const confidence = frame.confidence;
            const confidencePct = Math.round(confidence * 100);
            const fill = document.getElementById('confidenceFill');
            fill.style.width = confidencePct + '%';
            fill.className = 'confidence-fill';
            if (confidence >= 0.8) fill.classList.add('high');
            else if (confidence >= 0.5) fill.classList.add('medium');
            else fill.classList.add('low');
            document.getElementById('confidenceText').textContent = confidencePct + '%';

            // Update reasoning
            document.getElementById('reasoning').innerHTML = formatText(frame.reasoning);

            // Update concerns
            const concernsSection = document.getElementById('concernsSection');
            if (frame.concerns && frame.concerns.trim()) {{
                concernsSection.style.display = 'block';
                document.getElementById('concerns').innerHTML = formatText(frame.concerns);
            }} else {{
                concernsSection.style.display = 'none';
            }}

            // Update raw response
            document.getElementById('rawResponse').textContent = frame.raw_response;

            // Update controls
            document.getElementById('frameSlider').value = currentIndex;
            document.getElementById('frameInput').value = currentIndex;
            document.getElementById('frameLabel').textContent = currentIndex + ' / ' + (data.length - 1);

            // Update buttons
            document.getElementById('prevBtn').disabled = currentIndex === 0;
            document.getElementById('nextBtn').disabled = currentIndex === data.length - 1;
        }}

        function formatText(text) {{
            if (!text) return '-';
            // Convert bullet points
            text = text.replace(/^- /gm, '• ');
            // Convert line breaks to paragraphs
            return '<p>' + text.replace(/\\n\\n/g, '</p><p>').replace(/\\n/g, '<br>') + '</p>';
        }}

        function goToFrame(index) {{
            if (index >= 0 && index < data.length) {{
                currentIndex = index;
                updateDisplay();
            }}
        }}

        function nextFrame() {{
            if (currentIndex < data.length - 1) {{
                goToFrame(currentIndex + 1);
            }}
        }}

        function previousFrame() {{
            if (currentIndex > 0) {{
                goToFrame(currentIndex - 1);
            }}
        }}

        function playTimelapse() {{
            if (timelapseInterval) return;
            timelapseInterval = setInterval(() => {{
                if (currentIndex < data.length - 1) {{
                    nextFrame();
                }} else {{
                    stopTimelapse();
                }}
            }}, 500); // 2 frames per second
        }}

        function stopTimelapse() {{
            if (timelapseInterval) {{
                clearInterval(timelapseInterval);
                timelapseInterval = null;
            }}
        }}

        function toggleRawResponse() {{
            const raw = document.getElementById('rawResponse');
            const btn = event.target;
            if (raw.style.display === 'none') {{
                raw.style.display = 'block';
                btn.textContent = 'Hide Raw Response';
            }} else {{
                raw.style.display = 'none';
                btn.textContent = 'Show Raw Response';
            }}
        }}

        function togglePrompts() {{
            const prompts = document.getElementById('prompts');
            const btn = event.target;
            if (prompts.style.display === 'none') {{
                // Build the prompts display
                const frame = data[currentIndex];
                const userPrompt = USER_PROMPT_TEMPLATE
                    .replace('{{{{timepoint}}}}', frame.timepoint)
                    .replace('{{{{cell_count}}}}', frame.cell_count);

                prompts.innerHTML = `
                    <h3 style="color: #667eea; margin-top: 0;">System Prompt</h3>
                    <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 0.85rem;">${{SYSTEM_PROMPT}}</pre>

                    <h3 style="color: #667eea; margin-top: 1.5rem;">User Prompt (for this frame)</h3>
                    <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 0.85rem;">${{userPrompt}}</pre>
                `;
                prompts.style.display = 'block';
                btn.textContent = 'Hide Prompts';
            }} else {{
                prompts.style.display = 'none';
                btn.textContent = 'Show System & User Prompts';
            }}
        }}

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') {{
                previousFrame();
            }} else if (e.key === 'ArrowRight') {{
                nextFrame();
            }} else if (e.key === ' ') {{
                e.preventDefault();
                if (timelapseInterval) {{
                    stopTimelapse();
                }} else {{
                    playTimelapse();
                }}
            }}
        }});

        // Initialize
        updateDisplay();
    </script>
</body>
</html>
"""

    return html


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Create interactive HTML viewer for embryo classifications'
    )
    parser.add_argument(
        '--classifications',
        default='embryo_classifications_all.json',
        help='JSON file with classifications (default: embryo_classifications_all.json)'
    )
    parser.add_argument(
        '--output',
        default='embryo_viewer.html',
        help='Output HTML file (default: embryo_viewer.html)'
    )
    parser.add_argument(
        '--no-embed-images',
        action='store_true',
        help='Do not embed images (smaller file, but requires image files)'
    )

    args = parser.parse_args()

    create_html_viewer(
        classifications_file=args.classifications,
        output_file=args.output,
        include_images=not args.no_embed_images
    )
