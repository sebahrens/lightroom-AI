"""
Refactored prompt template for film photography analysis.
This version leverages a JSON-based prompt template for analyzing provided images.
"""

from typing import Dict, Any, List, Optional, Tuple

def get_json_image_analysis_prompt(include_film_analysis: bool = True) -> str:
    """
    Generate a standardized JSON prompt for film photography analysis using the refactored prompt template.
    
    This function creates a prompt that instructs an AI to analyze a provided image rather than
    relying on a textual description.

    Args:
        include_film_analysis: Whether to include film-specific analysis instructions.

    Returns:
        A formatted prompt string following the JSON-based template.
    """
    prompt = """
Below is a refactored version of the prompt. All references to XML tags have been replaced with a JSON structure, while preserving the original instructions and taxonomy. The final expected output should be a single JSON object following the format described.

---

**Instructions**  
You are an AI assistant specialized in evaluating the aesthetic quality of film photographs. Your task is to analyze the provided image, provide ratings across various dimensions, give an overall aesthetic rating, and categorize the image based on a specific taxonomy.

Please follow these steps to complete your analysis:

1. **Analyze Aesthetic Dimensions**  
   Evaluate the photograph based on the following six dimensions:  
   - Composition  
   - Lighting  
   - Color palette  
   - Subject matter  
   - Mood/atmosphere  
   - Technical execution  

   For each dimension, consider the following aspects:
   - **Composition**: Arrangement of elements, balance, use of space, adherence to or creative deviation from compositional rules.
   - **Lighting**: Quality, direction, and intensity of light; how it interacts with the subject and creates depth or atmosphere.
   - **Color palette**: Use of color (or lack thereof in black and white photos), color harmony, contribution to overall mood or message.
   - **Subject matter**: Choice of subject, uniqueness or universality, presentation within the context of the photograph.
   - **Mood/atmosphere**: Emotional impact, feelings evoked, effectiveness in communicating a particular mood.
   - **Technical execution**: Photographer's skill in using equipment, including