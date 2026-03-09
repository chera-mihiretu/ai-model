"""
Prompt templates for Story Bible AI generation.
"""

BIBLE_GENERATION_SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the Story Bible Architect. Your job is to generate specific, high-quality content for a writer's "Story Bible".

CONTEXT:
Project Title: {title}

PRIMARY SOURCE ({primary_source_label}):
{primary_source}

SECONDARY CONTEXT:
Characters: {characters}
{bible_context}
Current Writing Canvas:
{canvas_content}

TASK: {task_description}

RULES:
1. Stay consistent with all provided context, especially the PRIMARY SOURCE.
2. Focus on the specific tab's purpose.
3. Provide creative, evocative, and useful details.
4. NO conversational fluff (e.g., "I'd be happy to...").
5. Target the {genre} genre.

STRICT FORMATTING RULES - FOLLOW EXACTLY:
A. Output PLAIN TEXT ONLY. Your response is the content and nothing else.
B. NEVER use asterisks (*) or double asterisks (**) for emphasis, bold, italic, or any purpose.
C. NEVER use hashtags (#) or any header markers.
D. NEVER use dashes (-) or asterisks (*) as bullet points.
E. NEVER use underscores (_) for emphasis or decoration.
F. NEVER use backticks (`), blockquotes (>), or any other markdown syntax.
G. Use paragraph breaks and numbered lists (1. 2. 3.) for structure. No other formatting.
H. Write section titles as plain text on their own line without any decoration.
<|eot_id|>"""

PROMPTS = {
    "braindump": {
        "description": "Generate raw ideas, themes, and sparks based on the current context.",
        "task": "Generate a list of raw ideas, themes, concepts, and creative sparks that could expand this story. Focus on fragmented thoughts and interesting 'what-if' scenarios. No structure required."
    },
    "genre": {
        "description": "Suggest specific genres, sub-genres, tone, and stylistic expectations.",
        "task": "Suggest specific genre and sub-genre classifications for this story. Describe the ideal tone, target audience, and stylistic expectations. How should the mood feel for a reader?"
    },
    "worldbuilding": {
        "description": "Create locations, rules, culture, lore, or magic/tech systems.",
        "task": "Develop specific world-building details. This could include significant locations, societal rules, factions, magic/tech systems, or ancient lore. Ensure everything feels grounded in the story's logic."
    },
    "outline": {
        "description": "Generate acts, chapters, or story beats.",
        "task": "Generate a structured outline for the story progression. Include major acts, chapter summaries, or critical story beats. Ensure a clear narrative arc from beginning to end."
    },
    "synopsis": {
        "description": "Generate a high-level plot overview from the writer's braindump and genre.",
        "task": "Generate a concise but compelling synopsis from the writer's braindump ideas. Identify the core conflict, protagonist, stakes, and story arc from the braindump. Craft a cohesive narrative summary that introduces the characters, their goals, the central conflict, tone, themes, and unique elements. Write as flowing prose paragraphs without headers or labels."
    },
    "style": {
        "description": "Define writing style, tone, POV, and voice.",
        "task": "Generate a comprehensive style guide including: narrative POV (first person, third limited, omniscient), tense (past/present), tone (dark, humorous, serious, whimsical), prose style (sparse, lyrical, direct), pacing preferences, and voice characteristics that would suit this story based on the genre and context provided."
    }
}

def get_bible_prompt(section_key: str, title: str, characters: str, bible_context: str, canvas_content: str, genre: str, primary_source: str = "", primary_source_label: str = "Story Context") -> str:
    """Constructs the full prompt for a bible section with hierarchical source awareness."""
    if section_key not in PROMPTS:
        return ""
    
    config = PROMPTS[section_key]
    system = BIBLE_GENERATION_SYSTEM_PROMPT.format(
        title=title,
        primary_source_label=primary_source_label,
        primary_source=primary_source or "No primary source provided yet.",
        characters=characters,
        bible_context=bible_context,
        canvas_content=canvas_content,
        genre=genre,
        task_description=config['task']
    )
    
    return (
        f"{system}"
        f"<|start_header_id|>user<|end_header_id|>\n"
        f"Generate content for the '{section_key}' section of my Story Bible. "
        f"Base your generation primarily on the {primary_source_label} provided above.\n"
        f"<|eot_id|>\n"
        f"<|start_header_id|>assistant<|end_header_id|>"
    )
