import re

SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')


def split_into_sentences(text: str) -> list[str]:
    """Naive sentence splitter: breaks after . ! ? followed by whitespace.
    Not perfect (fails on abbreviations like "Dr. Smith", decimals like "3.14"),
    but simple, fast, and dependency-free — a reasonable trade-off, since
    occasional mis-splits don't meaningfully hurt retrieval quality."""
    sentences = SENTENCE_SPLIT_PATTERN.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _word_count(text: str) -> int:
    # Approximation of token count. A real tokenizer (e.g. the embedding
    # model's own tokenizer) would be more accurate, but word count is a
    # simple, dependency-free proxy that's good enough for sizing chunks.
    return len(text.split())


def chunk_text_by_sentences(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Greedily groups sentences into chunks up to chunk_size words, carrying
    the last ~chunk_overlap words forward into the next chunk for continuity."""
    sentences = split_into_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = _word_count(sentence)

        if current_word_count + sentence_words > chunk_size and current_sentences:
            chunks.append(" ".join(current_sentences))

            # Build overlap by walking backward through the chunk just closed,
            # collecting whole sentences until we've covered ~chunk_overlap words.
            overlap_sentences = []
            overlap_words = 0
            for s in reversed(current_sentences):
                overlap_sentences.insert(0, s)
                overlap_words += _word_count(s)
                if overlap_words >= chunk_overlap:
                    break

            current_sentences = overlap_sentences
            current_word_count = overlap_words

        current_sentences.append(sentence)
        current_word_count += sentence_words

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def chunk_document(pages: list[dict], chunk_size: int, chunk_overlap: int) -> list[dict]:
    """
    pages: [{"page_number": int | None, "text": str}, ...] — output of extract_document_text()
    Returns: [{"chunk_index": int, "page_number": int | None, "content": str, "token_count": int}, ...]

    Chunks are built PER PAGE, never spanning two pages, so every chunk maps to
    exactly one page number for citations.
    """
    all_chunks = []
    chunk_index = 0

    for page in pages:
        page_chunks = chunk_text_by_sentences(page["text"], chunk_size, chunk_overlap)
        for content in page_chunks:
            all_chunks.append({
                "chunk_index": chunk_index,
                "page_number": page["page_number"],
                "content": content,
                "token_count": _word_count(content),
            })
            chunk_index += 1

    return all_chunks