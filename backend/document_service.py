from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# Load env variables from root or local
load_dotenv()  # Check current folder
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")  # Check parent folder

if "GROQ_API_KEY" not in os.environ:
    raise ValueError("GROQ_API_KEY environment variable is not set!")

# ---------- LLM ----------
llm = ChatGroq(
    api_key=os.environ["GROQ_API_KEY"],
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=512,
    timeout=60,
)

# ---------- LOAD ALL DOCUMENTS ----------
docs = []

# Base path relative to this file
base_dir = Path(__file__).parent

# Load text files
text_folder = base_dir / "data" / "text_files"
if text_folder.exists():
    for txt_path in text_folder.glob("*.txt"):
        print(f"Loading TEXT -> {txt_path.name}")
        try:
            loader = TextLoader(str(txt_path), encoding="utf-8")
            docs.extend(loader.load())
        except Exception as e:
            print(f"Error loading {txt_path}: {e}")

# Load PDF files
pdf_folder = base_dir / "data" / "pdf"
if pdf_folder.exists():
    for pdf_path in pdf_folder.glob("*.pdf"):
        print(f"Loading PDF -> {pdf_path.name}")
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs.extend(loader.load())
        except Exception as e:
            print(f"Error loading {pdf_path}: {e}")

if not docs:
    print("⚠️ Warning: No documents loaded. Please place documents in data/text_files/ or data/pdf/")
    # Create a dummy doc to avoid FAISS initialization error
    docs = [Document(page_content="NeuraSearch AI Knowledge Base is empty.", metadata={"source": "system"})]

# ---------- SPLIT INTO CHUNKS ----------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80
)
chunks = splitter.split_documents(docs)

# ---------- BUILD VECTOR STORE ----------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_store = FAISS.from_documents(chunks, embeddings)

# MMR retriever
rag_retriever = vector_store.as_retriever(
    search_kwargs={"k": 20}
)

# ---------- RAG PIPELINE ----------
def query_rag(query: str, top_k: int = 6, min_score: float = 0.1):
    # Retrieve relevant chunks
    results = rag_retriever.invoke(query)
    
    # Build context
    context = "\n\n".join(doc.page_content for doc in results)
    
    if not context.strip():
        return {
            "answer": "⚠️ This information is not available in the uploaded documents.",
            "confidence": 0.0,
            "sources": [],
            "context": ""
        }
        
    prompt = f"""
You are a professional research assistant.

Use the CONTEXT to answer the QUESTION clearly, accurately.

If the CONTEXT is brief, expand the explanation naturally
but do not add new or unrelated information.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

    response = llm.invoke(prompt)
    answer = response.content if hasattr(response, "content") else response
    
    # Build sources
    sources = []
    seen_sources = set()
    for doc in results:
        src = doc.metadata.get("source", "unknown")
        # clean path to just filename
        if src != "unknown":
            src = Path(src).name
            
        page = str(doc.metadata.get("page", "-"))
        preview = doc.page_content[:250] + "..."
        
        # Avoid exact duplicate source-page previews in the sources list
        source_key = (src, page, doc.page_content[:100])
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append({
                "source": src,
                "page": page,
                "score": 1.0,
                "preview": preview
            })
            
    # Return top K sources
    sources = sources[:top_k]

    return {
        "answer": answer,
        "confidence": 0.90,
        "sources": sources,
        "context": context
    }
