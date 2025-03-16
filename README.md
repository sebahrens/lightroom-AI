# Lightroom AI Tool

A tool for enhancing Adobe Lightroom catalogs with AI-powered features.

## About

The Lightroom AI Tool works directly with Adobe Lightroom's catalog files (.lrcat), which are SQLite databases. By accessing this SQLite database, the tool can:

1. Extract information about images in your catalog
2. Locate and extract preview images from Lightroom's preview cache
3. Send these previews to Large Language Models (LLMs) for analysis
4. Generate descriptive keywords based on image content
5. Create aesthetic scores to help evaluate image quality
6. Write this information back to the Lightroom catalog

This non-destructive workflow enhances your Lightroom experience without altering your original images or compromising catalog integrity.

## Features

- **AI-powered image analysis**: Analyze images using various AI providers (Claude, OpenRouter, Ollama)
- **Batch processing**: Process multiple images efficiently
- **Keyword consolidation**: Organize and structure keywords hierarchically using AI

## Main Tool Functionality

The Lightroom AI Tool provides several key capabilities to enhance your Lightroom workflow:

### Image Analysis

- Automatically analyzes images in your Lightroom catalog using AI
- Extracts metadata such as camera settings, film stock identification, and visual attributes
- Supports multiple AI providers (Claude, OpenRouter, Ollama) with configurable options
- Generates descriptive keywords and tags based on image content

### Batch Processing

- Processes multiple images in parallel for efficient workflow
- Intelligently locates and extracts preview images from Lightroom catalog structure
- Tracks processing statistics and provides detailed progress reporting
- Monitors system resources to optimize performance

### Database Integration

- Seamlessly integrates with Lightroom's SQLite database
- Updates image metadata directly in the catalog
- Preserves catalog integrity while adding AI-generated information

## Keyword Consolidator Tool

The `lightroom_ai.cli_keyword_consolidator` is a specialized tool for organizing and structuring keywords in your Lightroom catalog:

### Key Features

- **Keyword Extraction**: Extracts all existing keywords from your Lightroom catalog
- **Normalization**: Cleans and normalizes keywords (removing duplicates, fixing capitalization, etc.)
- **Similarity Detection**: Groups similar keywords using both algorithmic and AI-powered methods
- **Hierarchical Organization**: Creates logical keyword hierarchies based on semantic relationships
- **Catalog Integration**: Updates your Lightroom catalog with the new keyword structure

### Usage

The keyword consolidator can be run as a standalone CLI tool to:
- Identify and merge duplicate or similar keywords
- Create parent-child relationships between related keywords
- Improve searchability and organization of your image library
- Reduce keyword clutter in your catalog

## Installation

### Prerequisites

- Python 3.8 or higher
- Adobe Lightroom Classic (tested with versions 10.0+)
- API keys for your chosen AI provider (Claude, OpenRouter, or local Ollama setup)

### Install from PyPI

