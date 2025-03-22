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
   - **Technical execution**: Photographer's skill in using equipment, including focus, exposure, and film choice (if visible).

2. **Provide Ratings**  
   For each dimension, give a score on a scale of 1 to 10 (where 1 is poor and 10 is excellent) along with brief reasoning for your evaluation.

3. **Overall Aesthetic Rating**  
   Provide an overall aesthetic rating for the photograph on the same 1–10 scale, considering all the individual dimension scores and your holistic impression.

4. **Categorize the Image**  
   Use the provided taxonomy to categorize the image based on:
   - Visual Subject (VS)
   - Image Characteristics (IC)
   - Contextual Elements (CE)

5. **Present Your Analysis**  
   Structure your **final** output entirely in JSON with the following top-level keys:
   - `detailed_evaluation`
   - `aesthetic_evaluation`
   - `taxonomy`

   **Example JSON Structure** (fill in your own reasoning, scores, and categories):

   ```json
   {
     "detailed_evaluation": {
       "dimensions": [
         {
           "name": "Composition",
           "key_elements": "[List key elements relevant to composition]",
           "positive_aspects": "[Positive points based on the image]",
           "negative_aspects": "[Negative points based on the image]",
           "contribution_to_score": "[Explain how these aspects affect the score]"
         },
         {
           "name": "Lighting",
           "key_elements": "[List key elements relevant to lighting]",
           "positive_aspects": "[Positive points based on the image]",
           "negative_aspects": "[Negative points based on the image]",
           "contribution_to_score": "[Explain how these aspects affect the score]"
         },
         {
           "name": "Color palette",
           "key_elements": "[List key elements relevant to color palette]",
           "positive_aspects": "[Positive points based on the image]",
           "negative_aspects": "[Negative points based on the image]",
           "contribution_to_score": "[Explain how these aspects affect the score]"
         },
         {
           "name": "Subject matter",
           "key_elements": "[List key elements relevant to subject matter]",
           "positive_aspects": "[Positive points based on the image]",
           "negative_aspects": "[Negative points based on the image]",
           "contribution_to_score": "[Explain how these aspects affect the score]"
         },
         {
           "name": "Mood/atmosphere",
           "key_elements": "[List key elements relevant to mood/atmosphere]",
           "positive_aspects": "[Positive points based on the image]",
           "negative_aspects": "[Negative points based on the image]",
           "contribution_to_score": "[Explain how these aspects affect the score]"
         },
         {
           "name": "Technical execution",
           "key_elements": "[List key elements relevant to technical execution]",
           "positive_aspects": "[Positive points based on the image]",
           "negative_aspects": "[Negative points based on the image]",
           "contribution_to_score": "[Explain how these aspects affect the score]"
         }
       ],
       "overall_rating": {
         "main_strengths": "[Summarize the main strengths across all dimensions]",
         "main_weaknesses": "[Summarize the main weaknesses across all dimensions]",
         "contribution_to_overall_score": "[Explain how strengths and weaknesses translate to the overall rating]"
       },
       "taxonomy_evaluation": {
         "vs_categories_considered": "[List potential Visual Subject categories and explain why they fit or not]",
         "ic_categories_considered": "[List potential Image Characteristics categories and explain why they fit or not]",
         "ce_categories_considered": "[List potential Contextual Elements categories and explain why they fit or not]"
       }
     },
     "aesthetic_evaluation": {
       "dimensions": [
         {
           "name": "Composition",
           "reasoning": "[Short reasoning for the final rating]",
           "score": 0
         },
         {
           "name": "Lighting",
           "reasoning": "[Short reasoning for the final rating]",
           "score": 0
         },
         {
           "name": "Color palette",
           "reasoning": "[Short reasoning for the final rating]",
           "score": 0
         },
         {
           "name": "Subject matter",
           "reasoning": "[Short reasoning for the final rating]",
           "score": 0
         },
         {
           "name": "Mood/atmosphere",
           "reasoning": "[Short reasoning for the final rating]",
           "score": 0
         },
         {
           "name": "Technical execution",
           "reasoning": "[Short reasoning for the final rating]",
           "score": 0
         }
       ],
       "overall_rating": {
         "reasoning": "[Brief justification for the overall rating]",
         "score": 0
       }
     },
     "taxonomy": {
       "VS": ["List of relevant Visual Subject codes"],
       "IC": ["List of relevant Image Characteristics codes"],
       "CE": ["List of relevant Contextual Elements codes"]
     }
   }
   ```

6. **Detailed Evaluation Section**  
   Before providing your final analysis inside `aesthetic_evaluation` and `taxonomy`, you must include a `detailed_evaluation` section with detailed reasoning:

   - **For each dimension**:
     1. List key elements from the image relevant to this dimension.
     2. Consider both positive and negative aspects of these elements.
     3. Explain how these elements contribute to the scoring for that dimension.
   - **For the overall rating**:
     1. Summarize the main strengths and weaknesses across all dimensions.
     2. Explain how these factors contribute to the overall aesthetic rating.
   - **For the taxonomy**:
     1. List potential categories for each of VS, IC, and CE.
     2. Explain why each category might or might not apply based on what you observe in the image.

---

**TAXONOMY REFERENCE**

When categorizing the image, use the following detailed taxonomy structure:

## Visual Subject (VS)

### VS1: People
- VS1.1: Individual Portrait
  - VS1.1.1: Close-up/Headshot
  - VS1.1.2: Half-body
  - VS1.1.3: Full-body
- VS1.2: Group
  - VS1.2.1: Small Group (2-4)
  - VS1.2.2: Medium Group (5-10)
  - VS1.2.3: Large Group (11+)
- VS1.3: Human Activity
  - VS1.3.1: Work/Occupation
  - VS1.3.2: Leisure/Recreation
  - VS1.3.3: Ceremony/Cultural Event
  - VS1.3.4: Daily Life

### VS2: Place
- VS2.1: Natural Environment
  - VS2.1.1: Mountain/Highland
  - VS2.1.2: Water Feature (Ocean, Lake, River)
  - VS2.1.3: Forest/Woodland
  - VS2.1.4: Desert/Arid
  - VS2.1.5: Sky/Weather Feature
- VS2.2: Built Environment
  - VS2.2.1: Exterior Architecture
  - VS2.2.2: Interior Space
  - VS2.2.3: Urban Street
  - VS2.2.4: Rural Setting
  - VS2.2.5: Transportation Infrastructure

### VS3: Objects
- VS3.1: Natural Objects
  - VS3.1.1: Flora (Plants, Flowers)
  - VS3.1.2: Fauna (Animals)
  - VS3.1.3: Rocks/Minerals/Terrain
- VS3.2: Manufactured Objects
  - VS3.2.1: Vehicles
  - VS3.2.2: Tools/Implements
  - VS3.2.3: Furnishings
  - VS3.2.4: Consumer Products
  - VS3.2.5: Art Objects

## Image Characteristics (IC)

### IC1: Composition
- IC1.1: Frame Arrangement
  - IC1.1.1: Symmetrical
  - IC1.1.2: Rule of Thirds
  - IC1.1.3: Centered Subject
  - IC1.1.4: Diagonals/Dynamic
- IC1.2: Perspective
  - IC1.2.1: Eye Level
  - IC1.2.2: High Angle
  - IC1.2.3: Low Angle
  - IC1.2.4: Bird's Eye
  - IC1.2.5: Worm's Eye
- IC1.3: Distance/Scale
  - IC1.3.1: Macro/Close-up
  - IC1.3.2: Mid-range
  - IC1.3.3: Wide Shot
  - IC1.3.4: Panoramic View

### IC2: Visual Style
- IC2.1: Tonality
  - IC2.1.1: Black & White
  - IC2.1.2: Monochrome (Sepia, Cyanotype, etc.)
  - IC2.1.3: Color Image
- IC2.2: Contrast
  - IC2.2.1: High Contrast
  - IC2.2.2: Medium Contrast
  - IC2.2.3: Low/Soft Contrast
- IC2.3: Focus
  - IC2.3.1: All-in-focus/Deep Depth
  - IC2.3.2: Selective Focus/Shallow Depth
  - IC2.3.3: Soft Focus/Diffused
  - IC2.3.4: Motion Blur

### IC3: Color Characteristics (if color)
- IC3.1: Color Temperature
  - IC3.1.1: Warm Tones
  - IC3.1.2: Cool Tones
  - IC3.1.3: Neutral
  - IC3.1.4: Mixed Temperature
- IC3.2: Color Saturation
  - IC3.2.1: Highly Saturated
  - IC3.2.2: Moderately Saturated
  - IC3.2.3: Desaturated/Muted
- IC3.3: Color Palette
  - IC3.3.1: Monochromatic
  - IC3.3.2: Complementary
  - IC3.3.3: Analogous
  - IC3.3.4: High Color Variety

## Contextual Elements (CE)

### CE1: Temporal Indicators
- CE1.1: Era Identifiers (Visually Apparent)
  - CE1.1.1: 1970s Aesthetic
  - CE1.1.2: 1980s Aesthetic
  - CE1.1.3: 1990s Aesthetic
  - CE1.1.4: 2000s Aesthetic
  - CE1.1.5: 2010-Present Aesthetic
- CE1.2: Time of Day
  - CE1.2.1: Dawn/Early Morning
  - CE1.2.2: Daytime
  - CE1.2.3: Golden Hour
  - CE1.2.4: Blue Hour/Twilight
  - CE1.2.5: Night
- CE1.3: Seasonal Indicators
  - CE1.3.1: Spring Elements
  - CE1.3.2: Summer Elements
  - CE1.3.3: Autumn Elements
  - CE1.3.4: Winter Elements

### CE2: Cultural Context
- CE2.1: Geographic Indicators
  - CE2.1.1: Recognizable Location/Landmark
  - CE2.1.2: Regional Architectural Style
  - CE2.1.3: Environmental Biome
  - CE2.1.4: Cultural Identifiers
- CE2.2: Social Context
  - CE2.2.1: Private/Personal
  - CE2.2.2: Public Event
  - CE2.2.3: Cultural Tradition
  - CE2.2.4: Professional/Occupational

### CE3: Photographic Condition
- CE3.1: Print Quality
  - CE3.1.1: Well-Preserved
  - CE3.1.2: Moderate Aging
  - CE3.1.3: Significant Aging/Damage
- CE3.2: Format Indicators
  - CE3.2.1: Square Format
  - CE3.2.2: Rectangular (3:2)
  - CE3.2.3: Rectangular (4:3)
  - CE3.2.4: Panoramic
- CE3.3: Photographic Genre
  - CE3.3.1: Documentary
  - CE3.3.2: Street Photography
  - CE3.3.3: Fine Art
  - CE3.3.4: Vernacular/Snapshot
  - CE3.3.5: Experimental

---
"""
    if include_film_analysis:
        prompt += """
For FILM FORMAT analysis, consider:
- If the image has a 3:2 aspect ratio with a distinctive 35mm grain pattern, it may indicate a "35mm" film format.
- If it has a square or near-square format (6x6), consider "120-6x6".
- If it's rectangular but wider than 35mm (6x4.5, 6x7, 6x9), select the appropriate 120 format.
- Look for film border edges, sprocket holes, or frame numbers that might be visible.
"""
    prompt += "\n---\n**Final Note**\nYour complete analysis must be presented as a **single JSON object** with three top-level keys: `detailed_evaluation`, `aesthetic_evaluation`, and `taxonomy`.\n"
    
    return prompt

def get_taxonomy_structure() -> Dict[str, Any]:
    """
    Returns the detailed taxonomy structure for film photography classification.
    
    Returns:
        A nested dictionary representing the full taxonomy hierarchy.
    """
    return {
        "VS": {  # Visual Subject
            "VS1": {
                "name": "People",
                "subcategories": {
                    "VS1.1": {
                        "name": "Individual Portrait",
                        "subcategories": {
                            "VS1.1.1": "Close-up/Headshot",
                            "VS1.1.2": "Half-body",
                            "VS1.1.3": "Full-body"
                        }
                    },
                    "VS1.2": {
                        "name": "Group",
                        "subcategories": {
                            "VS1.2.1": "Small Group (2-4)",
                            "VS1.2.2": "Medium Group (5-10)",
                            "VS1.2.3": "Large Group (11+)"
                        }
                    },
                    "VS1.3": {
                        "name": "Human Activity",
                        "subcategories": {
                            "VS1.3.1": "Work/Occupation",
                            "VS1.3.2": "Leisure/Recreation",
                            "VS1.3.3": "Ceremony/Cultural Event",
                            "VS1.3.4": "Daily Life"
                        }
                    }
                }
            },
            "VS2": {
                "name": "Place",
                "subcategories": {
                    "VS2.1": {
                        "name": "Natural Environment",
                        "subcategories": {
                            "VS2.1.1": "Mountain/Highland",
                            "VS2.1.2": "Water Feature (Ocean, Lake, River)",
                            "VS2.1.3": "Forest/Woodland",
                            "VS2.1.4": "Desert/Arid",
                            "VS2.1.5": "Sky/Weather Feature"
                        }
                    },
                    "VS2.2": {
                        "name": "Built Environment",
                        "subcategories": {
                            "VS2.2.1": "Exterior Architecture",
                            "VS2.2.2": "Interior Space",
                            "VS2.2.3": "Urban Street",
                            "VS2.2.4": "Rural Setting",
                            "VS2.2.5": "Transportation Infrastructure"
                        }
                    }
                }
            },
            "VS3": {
                "name": "Objects",
                "subcategories": {
                    "VS3.1": {
                        "name": "Natural Objects",
                        "subcategories": {
                            "VS3.1.1": "Flora (Plants, Flowers)",
                            "VS3.1.2": "Fauna (Animals)",
                            "VS3.1.3": "Rocks/Minerals/Terrain"
                        }
                    },
                    "VS3.2": {
                        "name": "Manufactured Objects",
                        "subcategories": {
                            "VS3.2.1": "Vehicles",
                            "VS3.2.2": "Tools/Implements",
                            "VS3.2.3": "Furnishings",
                            "VS3.2.4": "Consumer Products",
                            "VS3.2.5": "Art Objects"
                        }
                    }
                }
            }
        },
        "IC": {  # Image Characteristics
            "IC1": {
                "name": "Composition",
                "subcategories": {
                    "IC1.1": {
                        "name": "Frame Arrangement",
                        "subcategories": {
                            "IC1.1.1": "Symmetrical",
                            "IC1.1.2": "Rule of Thirds",
                            "IC1.1.3": "Centered Subject",
                            "IC1.1.4": "Diagonals/Dynamic"
                        }
                    },
                    "IC1.2": {
                        "name": "Perspective",
                        "subcategories": {
                            "IC1.2.1": "Eye Level",
                            "IC1.2.2": "High Angle",
                            "IC1.2.3": "Low Angle",
                            "IC1.2.4": "Bird's Eye",
                            "IC1.2.5": "Worm's Eye"
                        }
                    },
                    "IC1.3": {
                        "name": "Distance/Scale",
                        "subcategories": {
                            "IC1.3.1": "Macro/Close-up",
                            "IC1.3.2": "Mid-range",
                            "IC1.3.3": "Wide Shot",
                            "IC1.3.4": "Panoramic View"
                        }
                    }
                }
            },
            "IC2": {
                "name": "Visual Style",
                "subcategories": {
                    "IC2.1": {
                        "name": "Tonality",
                        "subcategories": {
                            "IC2.1.1": "Black & White",
                            "IC2.1.2": "Monochrome (Sepia, Cyanotype, etc.)",
                            "IC2.1.3": "Color Image"
                        }
                    },
                    "IC2.2": {
                        "name": "Contrast",
                        "subcategories": {
                            "IC2.2.1": "High Contrast",
                            "IC2.2.2": "Medium Contrast",
                            "IC2.2.3": "Low/Soft Contrast"
                        }
                    },
                    "IC2.3": {
                        "name": "Focus",
                        "subcategories": {
                            "IC2.3.1": "All-in-focus/Deep Depth",
                            "IC2.3.2": "Selective Focus/Shallow Depth",
                            "IC2.3.3": "Soft Focus/Diffused",
                            "IC2.3.4": "Motion Blur"
                        }
                    }
                }
            },
            "IC3": {
                "name": "Color Characteristics",
                "subcategories": {
                    "IC3.1": {
                        "name": "Color Temperature",
                        "subcategories": {
                            "IC3.1.1": "Warm Tones",
                            "IC3.1.2": "Cool Tones",
                            "IC3.1.3": "Neutral",
                            "IC3.1.4": "Mixed Temperature"
                        }
                    },
                    "IC3.2": {
                        "name": "Color Saturation",
                        "subcategories": {
                            "IC3.2.1": "Highly Saturated",
                            "IC3.2.2": "Moderately Saturated",
                            "IC3.2.3": "Desaturated/Muted"
                        }
                    },
                    "IC3.3": {
                        "name": "Color Palette",
                        "subcategories": {
                            "IC3.3.1": "Monochromatic",
                            "IC3.3.2": "Complementary",
                            "IC3.3.3": "Analogous",
                            "IC3.3.4": "High Color Variety"
                        }
                    }
                }
            }
        },
        "CE": {  # Contextual Elements
            "CE1": {
                "name": "Temporal Indicators",
                "subcategories": {
                    "CE1.1": {
                        "name": "Era Identifiers",
                        "subcategories": {
                            "CE1.1.1": "1970s Aesthetic",
                            "CE1.1.2": "1980s Aesthetic",
                            "CE1.1.3": "1990s Aesthetic",
                            "CE1.1.4": "2000s Aesthetic",
                            "CE1.1.5": "2010-Present Aesthetic"
                        }
                    },
                    "CE1.2": {
                        "name": "Time of Day",
                        "subcategories": {
                            "CE1.2.1": "Dawn/Early Morning",
                            "CE1.2.2": "Daytime",
                            "CE1.2.3": "Golden Hour",
                            "CE1.2.4": "Blue Hour/Twilight",
                            "CE1.2.5": "Night"
                        }
                    },
                    "CE1.3": {
                        "name": "Seasonal Indicators",
                        "subcategories": {
                            "CE1.3.1": "Spring Elements",
                            "CE1.3.2": "Summer Elements",
                            "CE1.3.3": "Autumn Elements",
                            "CE1.3.4": "Winter Elements"
                        }
                    }
                }
            },
            "CE2": {
                "name": "Cultural Context",
                "subcategories": {
                    "CE2.1": {
                        "name": "Geographic Indicators",
                        "subcategories": {
                            "CE2.1.1": "Recognizable Location/Landmark",
                            "CE2.1.2": "Regional Architectural Style",
                            "CE2.1.3": "Environmental Biome",
                            "CE2.1.4": "Cultural Identifiers"
                        }
                    },
                    "CE2.2": {
                        "name": "Social Context",
                        "subcategories": {
                            "CE2.2.1": "Private/Personal",
                            "CE2.2.2": "Public Event",
                            "CE2.2.3": "Cultural Tradition",
                            "CE2.2.4": "Professional/Occupational"
                        }
                    }
                }
            },
            "CE3": {
                "name": "Photographic Condition",
                "subcategories": {
                    "CE3.1": {
                        "name": "Print Quality",
                        "subcategories": {
                            "CE3.1.1": "Well-Preserved",
                            "CE3.1.2": "Moderate Aging",
                            "CE3.1.3": "Significant Aging/Damage"
                        }
                    },
                    "CE3.2": {
                        "name": "Format Indicators",
                        "subcategories": {
                            "CE3.2.1": "Square Format",
                            "CE3.2.2": "Rectangular (3:2)",
                            "CE3.2.3": "Rectangular (4:3)",
                            "CE3.2.4": "Panoramic"
                        }
                    },
                    "CE3.3": {
                        "name": "Photographic Genre",
                        "subcategories": {
                            "CE3.3.1": "Documentary",
                            "CE3.3.2": "Street Photography",
                            "CE3.3.3": "Fine Art",
                            "CE3.3.4": "Vernacular/Snapshot",
                            "CE3.3.5": "Experimental"
                        }
                    }
                }
            }
        }
    }

def get_taxonomy_flat_list() -> Dict[str, List[str]]:
    """
    Returns a flattened list of all taxonomy codes for each category.
    
    Returns:
        Dictionary with keys 'VS', 'IC', 'CE' and values as lists of all possible codes.
    """
    taxonomy = {
        "VS": [],  # Visual Subject codes
        "IC": [],  # Image Characteristics codes
        "CE": []   # Contextual Elements codes
    }
    
    # Visual Subject (VS) codes - including parent categories
    vs_codes = [
        "VS1", "VS1.1", "VS1.2", "VS1.3",  # Parent categories
        "VS2", "VS2.1", "VS2.2",  # Parent categories
        "VS3", "VS3.1", "VS3.2",  # Parent categories
        "VS1.1.1", "VS1.1.2", "VS1.1.3",  # Individual Portrait
        "VS1.2.1", "VS1.2.2", "VS1.2.3",  # Group
        "VS1.3.1", "VS1.3.2", "VS1.3.3", "VS1.3.4",  # Human Activity
        "VS2.1.1", "VS2.1.2", "VS2.1.3", "VS2.1.4", "VS2.1.5",  # Natural Environment
        "VS2.2.1", "VS2.2.2", "VS2.2.3", "VS2.2.4", "VS2.2.5",  # Built Environment
        "VS3.1.1", "VS3.1.2", "VS3.1.3",  # Natural Objects
        "VS3.2.1", "VS3.2.2", "VS3.2.3", "VS3.2.4", "VS3.2.5"   # Manufactured Objects
    ]
    taxonomy["VS"] = vs_codes
    
    # Image Characteristics (IC) codes - including parent categories
    ic_codes = [
        "IC1", "IC1.1", "IC1.2", "IC1.3",  # Parent categories
        "IC2", "IC2.1", "IC2.2", "IC2.3",  # Parent categories
        "IC3", "IC3.1", "IC3.2", "IC3.3",  # Parent categories
        "IC1.1.1", "IC1.1.2", "IC1.1.3", "IC1.1.4",  # Frame Arrangement
        "IC1.2.1", "IC1.2.2", "IC1.2.3", "IC1.2.4", "IC1.2.5",  # Perspective
        "IC1.3.1", "IC1.3.2", "IC1.3.3", "IC1.3.4",  # Distance/Scale
        "IC2.1.1", "IC2.1.2", "IC2.1.3",  # Tonality
        "IC2.2.1", "IC2.2.2", "IC2.2.3",  # Contrast
        "IC2.3.1", "IC2.3.2", "IC2.3.3", "IC2.3.4",  # Focus
        "IC3.1.1", "IC3.1.2", "IC3.1.3", "IC3.1.4",  # Color Temperature
        "IC3.2.1", "IC3.2.2", "IC3.2.3",  # Color Saturation
        "IC3.3.1", "IC3.3.2", "IC3.3.3", "IC3.3.4"   # Color Palette
    ]
    taxonomy["IC"] = ic_codes
    
    # Contextual Elements (CE) codes - including parent categories
    ce_codes = [
        "CE1", "CE1.1", "CE1.2", "CE1.3",  # Parent categories
        "CE2", "CE2.1", "CE2.2",  # Parent categories
        "CE3", "CE3.1", "CE3.2", "CE3.3",  # Parent categories
        "CE1.1.1", "CE1.1.2", "CE1.1.3", "CE1.1.4", "CE1.1.5",  # Era Identifiers
        "CE1.2.1", "CE1.2.2", "CE1.2.3", "CE1.2.4", "CE1.2.5",  # Time of Day
        "CE1.3.1", "CE1.3.2", "CE1.3.3", "CE1.3.4",  # Seasonal Indicators
        "CE2.1.1", "CE2.1.2", "CE2.1.3", "CE2.1.4",  # Geographic Indicators
        "CE2.2.1", "CE2.2.2", "CE2.2.3", "CE2.2.4",  # Social Context
        "CE3.1.1", "CE3.1.2", "CE3.1.3",  # Print Quality
        "CE3.2.1", "CE3.2.2", "CE3.2.3", "CE3.2.4",  # Format Indicators
        "CE3.3.1", "CE3.3.2", "CE3.3.3", "CE3.3.4", "CE3.3.5"   # Photographic Genre
    ]
    taxonomy["CE"] = ce_codes
    
    return taxonomy

def validate_taxonomy_codes(analysis_result: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates that the taxonomy codes used in the analysis result are valid.
    
    Args:
        analysis_result: The AI analysis result containing taxonomy codes.
        
    Returns:
        A tuple containing (is_valid, error_message)
    """
    valid_codes = get_taxonomy_flat_list()
    taxonomy = analysis_result.get("taxonomy", {})
    
    for category, codes in taxonomy.items():
        # Convert category to uppercase for case-insensitive comparison
        category_upper = category.upper()
        
        if category_upper not in valid_codes:
            return False, f"Invalid taxonomy category: {category}. Valid categories are: {', '.join(valid_codes.keys())}"
        
        # Check that all codes in the category are valid
        for code in codes:
            # Convert code to uppercase for case-insensitive comparison
            code_upper = code.upper()
            if code_upper not in valid_codes[category_upper]:
                return False, f"Invalid taxonomy code: {code} in category {category}"
    
    return True, None
