# ============================================================
# MEDIGUIDE AI - TEXT CHUNKING
# ============================================================

def split_text_into_chunks(text, chunk_size=500, overlap=50):

    if not text:
        return []

    text = " ".join(text.split())

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):

            last_period = chunk.rfind(".")
            last_space = chunk.rfind(" ")

            boundary = max(last_period, last_space)

            if boundary > chunk_size * 0.6:
                chunk = chunk[:boundary + 1]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        next_start = start + len(chunk) - overlap

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    sample_text = (
        "Patient Name: Ravi Kumar. "
        "Hemoglobin: 10.2 g/dL. "
        "Blood glucose: 120 mg/dL. "
        "Medicine: Paracetamol 500 mg. "
        "Doctor recommendation is written in the prescription."
    )

    chunks = split_text_into_chunks(
        sample_text,
        chunk_size=100,
        overlap=20
    )

    print("MEDIGUIDE AI - TEXT CHUNKING")
    print("============================")

    for i, chunk in enumerate(chunks, 1):
        print()
        print("Chunk", i)
        print("-------")
        print(chunk)