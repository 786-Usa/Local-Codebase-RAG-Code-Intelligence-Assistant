import os
import re
import ast
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

# Extension mapping to LangChain Language enums
LANGUAGE_MAP = {
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".py": Language.PYTHON,
    ".cpp": Language.CPP,
    ".html": Language.HTML
}

def extract_python_symbols(content: str):
    """Extracts function/class declarations and imported module names from Python AST."""
    symbols = []
    imports = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception:
        pass
    return list(set(symbols)), list(set(imports))

def extract_js_symbols(content: str):
    """Extracts function/class names and imported modules from JS/TS via regex patterns."""
    symbols = []
    imports = []
    
    # Match imports: import ... from 'module' or require('module')
    import_matches = re.findall(r'(?:import\s+.*?from\s+[\'"](.*?)[\'"]|require\([\'"](.*?)[\'"]\))', content)
    for m in import_matches:
        imp = m[0] or m[1]
        if imp:
            imports.append(imp)

    # Match functions and classes
    func_matches = re.findall(r'(?:function\s+([a-zA-Z0-9_]+)|class\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(|\b([a-zA-Z0-9_]+)\s*\()', content)
    for match in func_matches:
        for name in match:
            if name and name not in {"if", "for", "while", "switch", "catch", "require"}:
                symbols.append(name)
                
    return list(set(symbols)), list(set(imports))

def chunk_file(file_path: str, content: str):
    ext = os.path.splitext(file_path)[1].lower()
    lang = LANGUAGE_MAP.get(ext, None)

    # Extract symbols and imports based on file extension
    if ext == ".py":
        symbols, imports = extract_python_symbols(content)
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        symbols, imports = extract_js_symbols(content)
    else:
        symbols, imports = [], []

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
        metadatas=[{
            "file_path": file_path, 
            "extension": ext,
            "symbols": symbols,
            "imports": imports
        }]
    )
    return docs