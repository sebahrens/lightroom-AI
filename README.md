# Lightroom AI Tool

This repository provides a toolset for analyzing, keywording, and tagging photos in an Adobe Lightroom Classic catalog using AI services. By extracting Lightroom previews and sending them to various Large Language Model (LLM) providers (e.g., OpenRouter, Claude, Ollama), it enriches photo metadata with AI-driven insights, including keywords, aesthetic evaluations, and categorization according to a specialized film-photography taxonomy.

---

## Background & Motivation

Lightroom Classic users commonly face a challenge: large collections of images with incomplete or inconsistent metadata. Manual keyword entry can be time-consuming, and consistent labeling of large photo libraries is difficult. The **Lightroom AI Tool** addresses these issues by:

- **Extracting** preview images (or smart previews) from an `.lrcat` file (Lightroom catalog).
- **Sending** images to AI services for analysis (composition, color, subject matter, aesthetic rating, etc.).
- **Enhancing** the Lightroom catalog with automatically generated keywords, hierarchical tags, aesthetic scores, and more.

This approach helps photographers maintain a well-organized and richly annotated catalog without tedious manual tagging.

---

## Features

1. **Preview Extraction**  
   - Automatically locates previews (or uses smart previews/original images if previews are missing).
   - Employs multiple search strategies (UUID-based, filename-based, pattern-based, deep search, etc.).

2. **AI Integration**  
   - Integrates with multiple AI providers:
     - [OpenRouter](https://openrouter.ai)
     - [Claude API](https://www.anthropic.com/index/claude)
     - [Ollama (local LLAMA models)](https://ollama.ai)
   - Each provider can parse and return structured JSON containing keywords, tags, and aesthetic evaluations.

3. **Metadata Injection**  
   - Writes AI-generated keywords and tags back into the Lightroom catalog database.
   - Supports hierarchical keyword creation and advanced film photography taxonomies.
   - Optionally updates the **caption** and **rating** fields for quick in-Lightroom reference.

4. **Checkpointing & Resumability**  
   - Supports resuming interrupted runs through a checkpoint file that tracks processed images.
   - Avoids reprocessing images with existing “AI_Processed” keywords (or as recorded in the checkpoint).

5. **Parallel Batch Processing**  
   - Can utilize multiple CPU cores to process images in parallel, respecting memory constraints and concurrency.

6. **Keyword Consolidation**  
   - Optional step to further unify or consolidate overlapping keywords with LLM-based grouping (e.g., “sunset,” “sunsets,” “setting sun”).

---

## Installation

### 1. Clone or Download

Clone this repository or download a ZIP of it:

```bash
git clone https://github.com/yourusername/lightroom-ai-tool.git
cd lightroom-ai-tool
```

### 2. Python Environment

It is recommended to use Python 3.8+ in a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
```

### 3. Install Dependencies

Use pip to install all dependencies:

```bash
pip install -r requirements.txt
```

This installs:
- **requests**, **psutil**, **pillow**, **sqlite**-related libraries, 
- Providers (anthropic, openai, ollama) if needed.

### 4. Configure AI Provider

Create or modify **`config.json`** in the project root. You can reference the provided `config.json` or any example config. For instance, if you want to use OpenRouter:

```json
{
  "provider": "openrouter",
  "openrouter_api_key": "YOUR_OPENROUTER_API_KEY",
  "openrouter_model": "anthropic/claude-2",
  "openrouter_api_url": "https://openrouter.ai/api/v1/chat/completions",
  "openrouter_site_url": "https://example.com",
  "openrouter_title": "Lightroom AI Tool",
  
  "max_retries": 3,
  "batch_size": 10,
  "preview_max_resolution": 1024,
  "log_level": "INFO",
  "debug_mode": false,
  "use_smart_previews": true,
  ...
}
```

Adjust parameters such as `max_workers`, `memory_limit_mb`, `deep_search`, etc., to suit your system resources.

---

## Usage

You have two main ways to run the tool:

1. **Command-Line Interface (`cli.py`)**  
   Invoked via `python -m lightroom_ai.cli [options]`. This script scans your catalog, extracts previews, sends them to AI, and writes back metadata.

2. **Example Scripts (`examples/` Folder)**  
   The `examples/` directory shows typical usage patterns:
   - **example1_basic_usage.py**: Basic analysis of a catalog with default settings.
   - **example2_scan_only.py**: Just scans for previews without calling AI.
   - **example3_filtering.py**: Processes only certain images (e.g., matching a filename substring).
   - **example4_parallel_processing.py**: Speeds up analysis via parallel threads.
   - **example5_ollama_provider.py**: Using a local Ollama model.
   - **example6_database_analysis.py**: Debugging your Lightroom catalog structure.
   - **example7_resuming.py**: Demonstrates checkpoint-based resuming of long-running tasks.
   - **example_keyword_consolidator.py**: LLM-based grouping and hierarchical keyword creation.

### General Command-Line Example

```bash
# Basic usage from the CLI:
python -m lightroom_ai.cli \
    /path/to/LightroomCatalog.lrcat \
    --config config.json \
    --debug \
    --batch-size 5 \
    --max-workers 2
```

- **`catalog_path`**: The `.lrcat` file of your Lightroom library.
- **`--config`**: The path to your `config.json`.
- **`--debug`**: Enables debug logs.
- **`--batch-size`**: Number of images to process in each chunk.
- **`--max-workers`**: Parallel worker threads.

### Example 1: Basic Usage

```bash
cd examples
python example1_basic_usage.py /path/to/LightroomCatalog.lrcat
```

This:
1. Loads **`config.json`** at the project root.
2. Connects to the `.lrcat`.
3. Extracts standard (or smart) previews.
4. Sends them to your configured AI provider.
5. Inserts new keywords and caption details in the catalog.

### Example 2: Scan-Only Mode

If you want to check whether previews exist or need to be built:

```bash
python example2_scan_only.py /path/to/LightroomCatalog.lrcat --debug
```

### Example 3: Filtering

Process only images whose filenames contain `_RAW`:

```bash
python example3_filtering.py /path/to/LightroomCatalog.lrcat \
  --filter "_RAW"
```

---

## Keyword Consolidation

An optional **keyword consolidation** step uses an LLM to cluster synonyms or near-duplicates into canonical forms. It can also create hierarchical keyword structures for cleaner metadata in Lightroom. See:

```bash
cd examples
python example_keyword_consolidator.py /path/to/LightroomCatalog.lrcat
```

Configuration for the consolidation is read from the same or a separate `config.json`.

---

## Development & Testing

### 1. Setting Up Local Dev

```bash
git clone https://github.com/yourusername/lightroom-ai-tool.git
cd lightroom-ai-tool
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Running Tests

We use `pytest` for unit tests:

```bash
pytest --maxfail=1 --disable-warnings -q
```

Tests are located in `tests/`, covering:
- `batch_processor`
- `filesystem`
- `preview_extractor`
- `cli`
- etc.

### 3. Contributing

Pull requests are welcome. Submit bug fixes, improvements, or new features. Ensure your code is tested and linted. For major changes, open an issue first.

---

## Known Limitations & Future Enhancements

- **High concurrency** with large catalogs may hit SQLite locking. Consider reducing `max_workers` or using a more robust concurrency strategy.
- **LLM-based analysis** depends on the reliability of the AI model’s output. Incomplete or malformed JSON results in partial failures.
- **Film Analysis** is specialized—some prompts are tuned specifically for film photography taxonomy. Additional customizations may be needed for non-film usage.

---

## Acknowledgments

- [Adobe Lightroom Classic](https://www.adobe.com/products/photoshop-lightroom-classic.html) for the `.lrcat` database structure.
- [Anthropic Claude](https://www.anthropic.com/) & [OpenRouter](https://openrouter.ai) for the AI endpoints.
- [Pillow](https://pillow.readthedocs.io/) for image handling, [SQLite3](https://www.sqlite.org/index.html) for DB operations, etc.

---

## License

MIT License

Copyright (c) 2025 Sebastian Ahrens

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      
copies of the Software, and to permit persons to whom the Software is         
furnished to do so, subject to the following conditions:                       

The above copyright notice and this permission notice shall be included in     
all copies or substantial portions of the Software.                            

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR     
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,       
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER         
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN      
THE SOFTWARE.


---

**Enjoy a more organized Lightroom!** 

If you have any questions or run into issues, please open an [issue on GitHub](https://github.com/yourusername/lightroom-ai-tool/issues). Happy photo organizing!