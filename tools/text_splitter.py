# from langchain_text_splitters import RecursiveCharacterTextSplitter


# def split_text(text:str)-> list[str]:
#     """
#     Split the text into smaller chunks using RecursiveCharacterTextSplitter.
#     """
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=200,
#         length_function=len,
#     )
#     return text_splitter.split_text(text)