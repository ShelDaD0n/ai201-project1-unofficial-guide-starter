from sentence_transformers import SentenceTransformer
import chromadb
from ingest import load_chunks

COLLECTION_NAME = "vt_cs_reviews"

def build_vector_store():
    chunks = load_chunks()
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Delete collection if it exists so we start fresh
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    
    collection = client.create_collection(COLLECTION_NAME)

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"professor": c["professor"], "source": c["source"]} for c in chunks]

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    print(f"\nStored {collection.count()} chunks in ChromaDB.")
    return collection, model

if __name__ == "__main__":
    build_vector_store()