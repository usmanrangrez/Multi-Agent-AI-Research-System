def retrieve_chunks(
    question: str,
    chunks: list[str],
    top_k: int = 5,
) -> list[str]:

    query_words = set(question.lower().split())

    scored_chunks = []

    for chunk in chunks:
        chunk_words = set(chunk.lower().split())

        score = len(query_words & chunk_words)

        scored_chunks.append(
            (score, chunk)
        )

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        chunk
        for score, chunk in scored_chunks[:top_k]
        if score > 0
    ]