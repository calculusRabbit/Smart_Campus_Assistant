from transformers import pipeline
from retriever import embed_query, search_similar
import faiss
import json
import torch
from datetime import datetime
from config import GENERATION_MODEL, CHUNKS_PATH, INDEX_PATH, TOP_K


# load everything ONCE
print("Loading model...")
pipe = pipeline(
    "text-generation",
    model=GENERATION_MODEL,
    device_map="cuda"
)
print("Model loaded")

document_index = faiss.read_index(INDEX_PATH)
with open(CHUNKS_PATH, encoding="utf-8") as f:
    chunks = json.load(f)


def query_RAG(user_input: str, history: list) -> str:
    # retrieve relevant chunks
    query_vector = embed_query(user_input)
    distances, indices = search_similar(document_index, query_vector, top_k=TOP_K)

    # build relevant documents
    relevant_documents = ""
    sources_text = ""
    for idx, i in enumerate(indices):
        if i == -1:
            continue
        relevant_documents += chunks[i]["chunk_text"] + "\n\n"
        sources_text += f"[{idx+1}] {chunks[i]['title']}\n"
        sources_text += f" Score: {distances[idx]:.4f}\n"
        sources_text += f" URL: {chunks[i]['url']}\n\n"


    today = datetime.now().strftime("%B %d, %Y")
    system_instruction = f"You are a helpful assistant for WSU students. Today is {today}. Use the relevant documents to answer the question as best as you can. If you don't know the answer, say you don't know."

    messages = [{"role": "system", "content": system_instruction}]

    # add conversation history first
    for human, assistant in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": assistant})

    # add current question with relevant documents
    prompt = f"Question: {user_input}\n\nRelevant Documents:\n{relevant_documents}\n\nAnswer the question based on the relevant documents above."
    messages.append({"role": "user", "content": prompt})

    # generate answer
    output = pipe(
        messages,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True,
        top_p=0.9,
        repetition_penalty=1.2,
        return_full_text=False
    )
    answer = output[0]["generated_text"]
    return answer, sources_text


if __name__ == "__main__":
    print("WSU Campus Assistant ready! Type 'q' to quit\n")
    while True:
        question = input("You: ")
        if question.lower() == "q":
            break
        answer, _ = query_RAG(question, history=[])
        print(f"\nAssistant: {answer}\n")