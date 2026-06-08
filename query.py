import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq

load_dotenv()

COLLECTION_NAME = "vt_cs_reviews"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(COLLECTION_NAME)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def retrieve(query, k=4):
    embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=k)
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "professor": results["metadatas"][0][i]["professor"],
            "distance": results["distances"][0][i]
        })
    return chunks

def ask(question):
    chunks = retrieve(question)
    context = "\n\n".join([f"[Source: {c['source']}]\n{c['text']}" for c in chunks])
    sources = list(set(c["source"] for c in chunks))

    prompt = f"""You are a helpful assistant answering questions about Virginia Tech CS professors based solely on student reviews.

Use ONLY the information in the provided reviews to answer. Do not use any outside knowledge.
If the reviews don't contain enough information to answer, say "I don't have enough information on that."

Student Reviews:
{context}

Question: {question}
Answer:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
        "chunks": chunks
    }

if __name__ == "__main__":
    # Test retrieval with 3 of our evaluation questions
    test_queries = [
        "What weekly time commitment do students say is needed to get an A in Godmar Back's class?",
        "What do students say about Heath Hillman's teaching style?",
        "What grading decision made John Lewis popular with students?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("=" * 60)
        chunks = retrieve(query)
        for c in chunks:
            print(f"  [{c['distance']:.3f}] {c['professor']} | {c['text'][:100]}...")
        print()