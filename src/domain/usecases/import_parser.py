"""
Import Parser - Detects chapters in imported documents
"""
import re
from typing import List, Dict


class ImportParser:
    """Parse imported documents and detect chapter structure."""
    
    # Common chapter heading patterns
    CHAPTER_PATTERNS = [
        r'^#\s+Chapter\s+\d+',              # Markdown: # Chapter 1
        r'^##\s+Chapter\s+\d+',             # Markdown: ## Chapter 1
        r'^Chapter\s+\d+',                  # Plain: Chapter 1
        r'^CHAPTER\s+\d+',                  # Plain: CHAPTER 1
        r'^Ch\.\s+\d+',                     # Abbreviated: Ch. 1
        r'^Ch\s+\d+',                       # Abbreviated: Ch 1
        r'^\d+\.\s+[A-Z]',                  # Numbered: 1. Title
        r'^Part\s+\d+',                     # Part 1
        r'^PART\s+\d+',                     # PART 1
    ]
    
    @staticmethod
    def detect_chapters(content: str) -> List[Dict[str, str]]:
        """
        Detect chapters in document content.
        
        Returns:
            List of dicts with 'title' and 'content' keys
        """
        lines = content.split('\n')
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in lines:
            # Check if line matches any chapter pattern
            is_chapter = False
            for pattern in ImportParser.CHAPTER_PATTERNS:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_chapter = True
                    break
            
            if is_chapter:
                # Save previous chapter if exists
                if current_chapter:
                    chapters.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # Start new chapter
                current_chapter = line.strip()
                current_content = []
            else:
                # Add to current chapter content
                if current_chapter:
                    current_content.append(line)
        
        # Add final chapter
        if current_chapter:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content).strip()
            })
        
        # If no chapters detected, treat entire content as single chapter
        if not chapters:
            chapters.append({
                'title': 'Chapter 1',
                'content': content.strip()
            })
        
        return chapters
    
    @staticmethod
    def clean_chapter_title(title: str) -> str:
        """Clean up chapter title for display."""
        # Remove markdown headers
        title = re.sub(r'^#+\s*', '', title)
        # Remove extra whitespace
        title = ' '.join(title.split())
        # Capitalize properly if all caps
        if title.isupper() and len(title) > 10:
            title = title.title()
        return title or "Untitled Chapter"

