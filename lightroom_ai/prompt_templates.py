"""
Shared prompt templates for AI providers.
"""

from typing import Dict, List, Any, Optional

def get_image_analysis_prompt(categories: Dict[str, List[str]], include_film_analysis: bool = True) -> str:
    """
    Generate a standardized image analysis prompt with the given categories.
    
    Args:
        categories: Dictionary mapping category names to lists of allowed values
        include_film_analysis: Whether to include film-specific analysis instructions
        
    Returns:
        Formatted prompt string
    """
    # Start with the base prompt
    prompt = """Please analyze this photograph and categorize it according to these predefined categories.

"""
    # Add each category with its allowed values
    for category, values in categories.items():
        if values:
            # Format category name for display (e.g., 'film_format' → 'FILM FORMAT')
            category_display = category.replace('_', ' ').upper()
            
            # Customize instructions based on category
            if category == 'film_format':
                prompt += f"{category_display} (select the 1 most likely match):\n"
            elif category in ['film_characteristics', 'lens_characteristics', 'focal_length', 'aperture']:
                prompt += f"{category_display} (select up to 3 that apply):\n"
            else:
                prompt += f"{category_display} (select up to 2 best matches):\n"
            
            prompt += f"{', '.join(values)}\n\n"
    
    # Add film-specific instructions if requested
    if include_film_analysis:
        prompt += """
For FILM FORMAT analysis, consider:
- If the image has a 3:2 aspect ratio with distinctive 35mm grain pattern, select "35mm"
- If it has a square or near-square format (6x6), select "120-6x6"
- If it's rectangular but wider than 35mm (6x4.5, 6x7, 6x9), select the appropriate 120 format
- Look for film border edges, sprocket holes, or frame numbers that might be visible

For LENS CHARACTERISTICS, consider:
- Perspective distortion (wide-angle vs. telephoto compression)
- Depth of field and bokeh qualities (lens speed indicators)
- Sharpness, contrast, and rendering characteristics
- Any distinctive lens signatures (swirly bokeh, particular flare patterns)
"""

    # Add aesthetic score instructions
    prompt += """
Also provide an aesthetic score from 0 to 10, where 10 represents exceptional artistic quality.

Return ONLY a JSON object with this structure:
{
"""
    
    # Add each category to the requested JSON structure
    for category in categories.keys():
        prompt += f'  "{category}": [...],\n'
        
    prompt += """  "keywords": [...],
  "tags": [...],
  "aesthetic_score": ...
}

IMPORTANT:
1. For each category, select ONLY from the provided values
2. If a category doesn't apply, include an empty array
3. Do not create new categories or values
4. Include 5-10 general keywords in the "keywords" field
5. Include 5-10 style/mood tags in the "tags" field
6. Respond with valid JSON only
"""
    
    return prompt

def get_default_categories() -> Dict[str, List[str]]:
    """
    Get the default set of categories and their allowed values.
    
    Returns:
        Dictionary mapping category names to lists of allowed values
    """
    return {
        "film_format": [
            "35mm", "120-6x4.5", "120-6x6", "120-6x7", "120-6x9", "4x5", "8x10", "digital"
        ],
        "film_characteristics": [
            "color", "black & white", "fine grain", "medium grain", "coarse grain", 
            "high contrast", "low contrast", "neutral", "saturated", "muted"
        ],
        "lens_characteristics": [
            "sharp", "soft", "bokeh", "distortion", "vignetting", "flare", 
            "chromatic aberration", "high contrast", "low contrast"
        ],
        "focal_length": [
            "ultra-wide", "wide", "normal", "telephoto", "super-telephoto"
        ],
        "aperture": [
            "wide open", "shallow depth of field", "medium depth of field", "deep depth of field", 
            "f/1.4", "f/2", "f/2.8", "f/4", "f/5.6", "f/8", "f/11", "f/16", "f/22"
        ],
        "content_type": [
            "portrait", "landscape", "street", "architecture", "still life", 
            "abstract", "documentary", "wildlife", "macro", "night", "aerial"
        ],
        "main_subject": [
            "person", "group", "building", "nature", "animal", "plant", 
            "object", "vehicle", "pattern", "texture"
        ],
        "lighting": [
            "natural", "artificial", "bright", "dark", "backlit", "side-lit", 
            "front-lit", "soft", "harsh", "high-key", "low-key", "golden hour", "blue hour"
        ],
        "color": [
            "vibrant", "muted", "monochrome", "warm", "cool", "complementary", 
            "analogous", "pastel", "saturated", "desaturated"
        ],
        "mood": [
            "happy", "sad", "peaceful", "energetic", "mysterious", "romantic", 
            "dramatic", "nostalgic", "tense", "serene", "melancholic"
        ],
        "style": [
            "documentary", "fine art", "commercial", "editorial", "minimalist", 
            "experimental", "vintage", "modern", "classic", "surreal"
        ]
    }

def format_analysis_result(raw_result: Dict[str, Any], categories: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Format the AI analysis result into a standardized structure.
    
    Args:
        raw_result: Raw AI result with categories
        categories: Dictionary of allowed categories
        
    Returns:
        Formatted result compatible with the application
    """
    # Initialize the formatted result
    formatted_result = {
        "keywords": [],
        "tags": [],
        "aesthetic_score": 0,
        "categories": {}
    }
    
    # Extract aesthetic score
    if "aesthetic_score" in raw_result:
        try:
            score = float(raw_result["aesthetic_score"])
            formatted_result["aesthetic_score"] = min(max(score, 0), 10)  # Clamp between 0-10
        except (ValueError, TypeError):
            pass
    
    # Extract keywords and tags if provided directly
    if "keywords" in raw_result and isinstance(raw_result["keywords"], list):
        formatted_result["keywords"] = raw_result["keywords"]
    
    if "tags" in raw_result and isinstance(raw_result["tags"], list):
        formatted_result["tags"] = raw_result["tags"]
    
    # Process each category
    for category in categories.keys():
        # Get values for this category, ensuring they're from the allowed list
        if category in raw_result and isinstance(raw_result[category], list):
            # Filter to only include allowed values
            allowed_values = set(categories[category])
            valid_values = [v for v in raw_result[category] if v in allowed_values]
            
            # Store in the formatted result
            formatted_result["categories"][category] = valid_values
            
            # If keywords/tags weren't provided directly, build them from categories
            if not formatted_result["keywords"] and category in ["content_type", "main_subject"]:
                formatted_result["keywords"].extend(valid_values)
            
            if not formatted_result["tags"] and category in ["style", "mood", "color"]:
                formatted_result["tags"].extend(valid_values)
    
    return formatted_result
