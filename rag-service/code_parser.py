import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

LANGUAGE_MAP = {
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".py": Language.PYTHON,
    ".cpp": Language.CPP,
    ".html": Language.HTML
}

def chunk_file(file_path: str, content: str):
    # Cap maximum file content length to prevent thread locks on giant files
    if len(content) > 100000:
        content = content[:100000]

    ext = os.path.splitext(file_path)[1].lower()
    lang = LANGUAGE_MAP.get(ext, None)

    if lang:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang,
            chunk_size=600,
            chunk_overlap=100
        )
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100
        )

    docs = splitter.create_documents(
        texts=[content],
        metadatas=[{"file_path": file_path, "extension": ext}]
    )
    return docs