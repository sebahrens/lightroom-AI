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
- **Resumable processing**: Continue from where you left off with checkpoint management
- **Film stock identification**: Automatically identify film stocks and their characteristics
- **Customizable prompts**: Tailor the AI analysis to your specific needs

## Installation

