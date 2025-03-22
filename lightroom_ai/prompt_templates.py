"""
Shared prompt templates for AI providers.
"""

from typing import Dict, List, Any, Optional
from .film_analysis import get_json_image_analysis_prompt, validate_taxonomy_codes, get_taxonomy_structure
from .logging_setup import get_logger

logger = get_logger(__name__)

def get_image_analysis_prompt(include_film_analysis: bool = True) -> str:
    """
    Generate a standardized image analysis prompt for film photography.
    
    Args:
        include_film_analysis: Whether to include film-specific analysis instructions
        
    Returns:
        Formatted prompt string
    """
    return get_json_image_analysis_prompt(include_film_analysis)

def format_analysis_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the AI analysis result into a standardized structure.
    
    Args:
        raw_result: Raw AI result with taxonomy and aesthetic evaluation
        
    Returns:
        Formatted result compatible with the application
    """
    # Initialize the formatted result
    formatted_result = {
        "keywords": [],
        "tags": [],
        "aesthetic_score": 0,
        "categories": {},
        "taxonomy": {},
        "detailed_evaluation": {}
    }
    
    # Extract aesthetic score
    if "aesthetic_evaluation" in raw_result and "overall_rating" in raw_result["aesthetic_evaluation"]:
        try:
            score = float(raw_result["aesthetic_evaluation"]["overall_rating"]["score"])
            formatted_result["aesthetic_score"] = min(max(score, 0), 10)  # Clamp between 0-10
        except (ValueError, TypeError, KeyError):
            logger.warning("Could not extract aesthetic score from analysis result")
    
    # Extract taxonomy information
    if "taxonomy" in raw_result:
        formatted_result["taxonomy"] = raw_result["taxonomy"]
        
        # Generate keywords and tags from taxonomy codes
        vs_codes = raw_result["taxonomy"].get("vs", [])
        ic_codes = raw_result["taxonomy"].get("ic", [])
        ce_codes = raw_result["taxonomy"].get("ce", [])
        
        # Map Visual Subject codes to keywords
        keyword_mapping = {
            "VS1.1": "portrait",
            "VS1.2": "group",
            "VS1.3": "people",
            "VS2.1": "nature",
            "VS2.2": "architecture",
            "VS3.1.1": "plant",
            "VS3.1.2": "animal",
            "VS3.2": "object"
        }
        
        for code in vs_codes:
            for prefix, keyword in keyword_mapping.items():
                if code.startswith(prefix) and keyword not in formatted_result["keywords"]:
                    formatted_result["keywords"].append(keyword)
        
        # Map Image Characteristics to tags
        ic_tag_mapping = {
            "IC2.1.1": "black & white",
            "IC2.1.2": "monochrome",
            "IC2.2.1": "high contrast",
            "IC2.2.3": "low contrast",
            "IC3.1.1": "warm",
            "IC3.1.2": "cool",
            "IC3.2.1": "saturated",
            "IC3.2.3": "muted"
        }
        
        for code in ic_codes:
            if code in ic_tag_mapping and ic_tag_mapping[code] not in formatted_result["tags"]:
                formatted_result["tags"].append(ic_tag_mapping[code])
        
        # Map Contextual Elements to tags
        ce_tag_mapping = {
            "CE1.2.3": "golden hour",
            "CE1.2.4": "blue hour",
            "CE1.2.5": "night",
            "CE3.3.1": "documentary",
            "CE3.3.2": "street",
            "CE3.3.3": "fine art",
            "CE3.3.4": "snapshot",
            "CE3.3.5": "experimental"
        }
        
        for code in ce_codes:
            if code in ce_tag_mapping and ce_tag_mapping[code] not in formatted_result["tags"]:
                formatted_result["tags"].append(ce_tag_mapping[code])
        
        # Map to categories structure for compatibility with existing code
        formatted_result["categories"] = {
            "film_format": [],
            "film_characteristics": [],
            "lens_characteristics": [],
            "focal_length": [],
            "aperture": [],
            "content_type": [],
            "main_subject": [],
            "lighting": [],
            "color": [],
            "mood": [],
            "style": []
        }
        
        # Film format
        if any(code.startswith("CE3.2") for code in ce_codes):
            if "CE3.2.1" in ce_codes:  # Square Format
                formatted_result["categories"]["film_format"].append("120-6x6")
            elif "CE3.2.2" in ce_codes:  # Rectangular (3:2)
                formatted_result["categories"]["film_format"].append("35mm")
            elif "CE3.2.4" in ce_codes:  # Panoramic
                formatted_result["categories"]["film_format"].append("120-6x9")
        
        # Film characteristics
        if "IC2.1.1" in ic_codes:  # Black & White
            formatted_result["categories"]["film_characteristics"].append("black & white")
        elif "IC2.1.3" in ic_codes:  # Color Image
            formatted_result["categories"]["film_characteristics"].append("color")
        
        if "IC2.2.1" in ic_codes:  # High Contrast
            formatted_result["categories"]["film_characteristics"].append("high contrast")
        elif "IC2.2.3" in ic_codes:  # Low/Soft Contrast
            formatted_result["categories"]["film_characteristics"].append("low contrast")
        
        # Content type
        if any(code.startswith("VS1.1") for code in vs_codes):  # Individual Portrait
            formatted_result["categories"]["content_type"].append("portrait")
        if any(code.startswith("VS2.1") for code in vs_codes):  # Natural Environment
            formatted_result["categories"]["content_type"].append("landscape")
        if "VS2.2.3" in vs_codes:  # Urban Street
            formatted_result["categories"]["content_type"].append("street")
        if any(code.startswith("VS2.2.1") for code in vs_codes):  # Exterior Architecture
            formatted_result["categories"]["content_type"].append("architecture")
        if "CE3.3.1" in ce_codes:  # Documentary
            formatted_result["categories"]["content_type"].append("documentary")
    
    # Extract detailed evaluation
    if "detailed_evaluation" in raw_result:
        formatted_result["detailed_evaluation"] = raw_result["detailed_evaluation"]
    
    # Extract aesthetic evaluation
    if "aesthetic_evaluation" in raw_result:
        formatted_result["aesthetic_evaluation"] = raw_result["aesthetic_evaluation"]
    
    # Validate the taxonomy codes
    is_valid, error_message = validate_taxonomy_codes(raw_result)
    if not is_valid:
        logger.warning(f"Invalid taxonomy codes in analysis result: {error_message}")
    
    return formatted_result
