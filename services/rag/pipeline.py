import json
import os
from datetime import datetime

import faiss
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from services.rag.config import (
    CHUNKS_PATH,
    GENERATION_MODEL,
    INDEX_PATH,
    TOP_K,
)
from services.rag.retriever import embed_query, search_similar

load_dotenv()

hf_token = os.getenv("HF_TOKEN")
client = InferenceClient(
    provider="featherless-ai",
    token=hf_token,
)

document_index = faiss.read_index(str(INDEX_PATH))
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
    system_instruction = (
    f"You are a helpful assistant for WSU students. Today is {today}. "
    "Use the relevant documents to answer the question as best as you can. "
    "If you don't know the answer, say you don't know."
    )

    messages = [{"role": "system", "content": system_instruction}]

    # add conversation history first
    for human, assistant in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": assistant})

    # add current question with relevant documents
    prompt = (
    f"Question: {user_input}\n\n"
    f"Relevant Documents:\n{relevant_documents}\n\n"
    "Answer the question based on the relevant documents above."
    )
    messages.append({"role": "user", "content": prompt})

    # Generate the answer using remote Hugging Face inference
    response = client.chat_completion(
        messages=messages,
        model=GENERATION_MODEL,
        max_tokens=512,
        temperature=0.7,
        top_p=0.9,
    )

    answer = response.choices[0].message.content
    return answer, sources_text


if __name__ == "__main__":
    print("WSU Campus Assistant ready! Type 'q' to quit\n")
    while True:
        question = input("You: ")
        if question.lower() == "q":
            break
        answer, _ = query_RAG(question, history=[])
        print(f"\nAssistant: {answer}\n")