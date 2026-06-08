import os
import re

DOCS_DIR = "docs"

def load_chunks(docs_dir=DOCS_DIR):
    chunks = []

    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        # Extract professor name from the header line
        professor = "Unknown"
        for line in raw.splitlines():
            if line.startswith("Professor:"):
                professor = line.replace("Professor:", "").strip()
                break

        # Split on review bullets — lines starting with "-"
        # Join the full file, then split on newline-dash pattern
        reviews_section = raw.split("Reviews:")[-1]
        raw_reviews = re.split(r'\n-', reviews_section)

        for i, review in enumerate(raw_reviews):
            text = review.strip().lstrip("-").strip()
            if len(text) < 20:  # skip empty or near-empty
                continue
            chunks.append({
                "text": text,
                "professor": professor,
                "source": filename,
                "chunk_index": i
            })

    return chunks


if __name__ == "__main__":
    chunks = load_chunks()
    print(f"\nTotal chunks: {len(chunks)}\n")
    print("=" * 60)
    print("5 SAMPLE CHUNKS:")
    print("=" * 60)
    for chunk in chunks[:5]:
        print(f"\nProfessor: {chunk['professor']}")
        print(f"Source:    {chunk['source']}")
        print(f"Index:     {chunk['chunk_index']}")
        print(f"Text:      {chunk['text']}")
        print("-" * 60)