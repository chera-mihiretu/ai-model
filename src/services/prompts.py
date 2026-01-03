"""
Prompt templates for Story Bible AI generation.
"""

BIBLE_GENERATION_SYSTEM_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the Story Bible Architect. Your job is to generate specific, high-quality content for a writer's "Story Bible".

CONTEXT:
Project Title: {title}
Characters: {characters}
Other Bible Sections:
{bible_context}
Current Writing Canvas:
{canvas_content}

TASK: {task_description}

RULES:
1. Stay consistent with all provided context.
2. Focus on the specific tab's purpose.
3. Provide creative, evocative, and useful details.
4. NO conversational fluff (e.g., "I'd be happy to...").
5. Format the output clearly.
6. Target the {genre} genre.
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
        "description": "Generate a high-level plot overview.",
        "task": "Generate a concise but compelling synopsis of the main plot. Focus on the core conflict, the protagonist's journey, and the stakes."
    }
}

def get_bible_prompt(section_key: str, title: str, characters: str, bible_context: str, canvas_content: str, genre: str) -> str:
    """Constructs the full prompt for a bible section."""
    if section_key not in PROMPTS:
        return ""
    
    config = PROMPTS[section_key]
    system = BIBLE_GENERATION_SYSTEM_PROMPT.format(
        title=title,
        characters=characters,
        bible_context=bible_context,
        canvas_content=canvas_content,
        genre=genre,
        task_description=config['task']
    )
    
    return (
        f"{system}"
        f"<|start_header_id|>user<|end_header_id|>\n"
        f"Generate content for the '{section_key}' section of my Story Bible.\n"
        f"<|eot_id|>\n"
        f"<|start_header_id|>assistant<|end_header_id|>"
    )
