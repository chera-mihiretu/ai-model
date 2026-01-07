import re

def split_text_into_chunks(text, max_chars=250):
    print(f"Original Text Length: {len(text)}")
    
    # Current IMPL roughly simulation
    # sentences = text.replace('\n', ' ').split('. ')
    
    # Proposed Regex IMPL
    # Split by common sentence terminators but keep them
    # (?<=[.!?])\s+
    
    # Let's test the current one first to see if it fails
    sentences_current = text.replace('\n', ' ').split('. ')
    chunks_current = []
    current_chunk = []
    current_len = 0
    
    print(f"Split count (Basic): {len(sentences_current)}")
    
    for s in sentences_current:
        s_len = len(s)
        if current_len + s_len < max_chars:
            current_chunk.append(s)
            current_len += s_len
        else:
            chunks_current.append(". ".join(current_chunk) + ".")
            current_chunk = [s]
            current_len = s_len
            
    if current_chunk:
        chunks_current.append(". ".join(current_chunk) + ".")
        
    print("\n--- Current Logic Results ---")
    for i, c in enumerate(chunks_current):
        print(f"Chunk {i}: len={len(c)} | Content: {c[:50]}...")
        
    return chunks_current

sample_text = """This is the first sentence.
This is the second sentence which is on a new line.
Here is a third sentence that implies a paragraph continuation.
But what if we have a very long sentence that goes on and on and on and lacks proper punctuation for a while and just keeps going to test the limit of the chunker?
This is the final sentence."""

split_text_into_chunks(sample_text)
