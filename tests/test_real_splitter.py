# from tools.retriever import retrieve_chunks
# from tools.text_splitter import split_text
# from tools.web_reader import read_webpage

# url = "https://arxiv.org/html/2507.18910v1"

# text = read_webpage.invoke(url)

# chunks = split_text(text)

# question = "What are the latest developments in RAG?"

# relevant_chunks = retrieve_chunks(
#     question,
#     chunks,
#     top_k=5,
# )

# print(f"\nTOTAL CHUNKS: {len(chunks)}")
# print(f"RELEVANT CHUNKS: {len(relevant_chunks)}")

# for index, chunk in enumerate(relevant_chunks):
#     print(f"\n--- RELEVANT CHUNK {index} ---")
#     print(chunk)