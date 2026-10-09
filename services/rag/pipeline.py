import json
from datetime import datetime

import faiss
import httpx

from services.rag.config import (
    CHUNKS_PATH,
    GENERATION_MODEL,
    INDEX_PATH,
    OLLAMA_URL,
    TOP_K,
)
from services.rag.retriever import embed_query, search_similar

document_index = faiss.read_index(str(INDEX_PATH))
with open(CHUNKS_PATH, encoding="utf-8") as f:
    chunks = json.load(f)

def generate_with_ollama(messages: list[dict]) -> str:
    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": GENERATION_MODEL,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": 512,
            },
        },
        timeout=120.0,
    )
    response.raise_for_status()

    data = response.json()
    content = data["message"]["content"]

    # Qwen3 may include internal reasoning before </think>.
    if "</think>" in content:
        content = content.split("</think>", 1)[1]

    return content.strip()

def is_bad_generation(answer: str) -> bool:
    if not answer or not answer.strip():
        return True

    normalized = answer.strip().lower()

    # Reject incomplete Qwen3 thinking output.
    if "<think>" in normalized or "</think>" in normalized:
        return True

    # Detect common reasoning-style openings.
    reasoning_prefixes = (
        "okay, let me",
        "let me think",
        "let me analyze",
        "the user is asking",
        "the user wants",
        "i need to check",
        "looking at the documents",
        "first, i need to",
    )

    if normalized.startswith(reasoning_prefixes):
        return True

    # Preserve the existing repetition detection.
    most_common_count = max(answer.count(char) for char in set(answer))
    repetition_ratio = most_common_count / len(answer)

    return repetition_ratio > 0.5

def query_RAG(user_input: str, history: list) -> tuple[str, str]:
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
        "You are a helpful assistant for Wichita State University students. "
        f"Today is {today}. "
        "Answer using only the relevant documents provided. "
        "Give a direct and concise answer, usually 2 to 4 sentences. "
        "Do not describe your reasoning process or discuss irrelevant documents. "
        "If the documents do not contain enough information to answer the question, "
        "clearly say that the information was not found in the available documents. "
        "Do not claim that a club, event, service, or resource does not exist "
        "just because it is not mentioned in the documents. "
        "Never invent information that is not supported by the documents."
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
    "Answer the question directly using the relevant documents above. "
    "Keep the answer concise."
    )
    messages.append({"role": "user", "content": prompt})

    # Generate the answer using local Ollama inference
    try:
        answer = generate_with_ollama(messages)

        if is_bad_generation(answer):
            print("First RAG generation was unreliable. Retrying with a focused prompt.")

            retry_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a Wichita State University campus assistant. "
                        "Provide only the final answer. "
                        "Do not include reasoning, analysis, or thinking tags. "
                        "Use only the supplied campus documents. "
                        "If the documents do not contain enough information, "
                        "say that the information was not found in the available documents. "
                        "Do not claim that a club, event, service, or resource does not exist "
                        "just because it is not mentioned in the documents. "
                        "Never invent information that is not supported by the documents."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Campus documents:\n{relevant_documents}\n\n"
                        f"Student question: {user_input}\n\n"
                        "Write a concise answer in 2 to 4 sentences. "
                        "Output only the answer."
                    ),
                },
            ]

            answer = generate_with_ollama(retry_messages)

            if is_bad_generation(answer):
                answer = (
                    "I couldn't generate a reliable answer right now. "
                    "Please try asking your question again."
                )

    except (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.HTTPStatusError,
    ) as exc:
        print(f"Ollama generation error: {exc}")
        answer = (
            "I found relevant campus information, but the AI generation "
            "service is temporarily unavailable. Please try again in a moment."
        )
    return answer, sources_text


if __name__ == "__main__":
    print("WSU Campus Assistant ready! Type 'q' to quit\n")
    while True:
        question = input("You: ")
        if question.lower() == "q":
            break
        answer, _ = query_RAG(question, history=[])
        print(f"\nAssistant: {answer}\n")