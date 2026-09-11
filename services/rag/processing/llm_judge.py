import re
import json
import os
from transformers import pipeline
from processing.prompt import SYSTEM_INSTRUCTIONS, TASK_PROMPT
import torch
from config import JUDGE_MODEL, RAW_DATA_PATH, FILTERED_DIR
import torch.multiprocessing as mp
threshold = 0.35
output_dir = FILTERED_DIR
input_file = RAW_DATA_PATH
num_gpus = 4


def parse_json(raw: str) -> tuple[float, str]:
    try:
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = float(data.get("score", 0.5))
            reason = data.get("reason", "")
            return score, reason
    except json.JSONDecodeError:
        pass
    except ValueError:
        pass
    return 0.5, "parse error"

def get_score(raw_content: str, model) ->tuple[float, str]:

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": TASK_PROMPT.format(text=raw_content)},
    ]

    output = model(
        messages,
        max_new_tokens=64,
        temperature=0.1,
        top_p=0.8,
        top_k=20,
        do_sample=True,
        return_full_text=False
    )

    raw = output[0]["generated_text"].strip()
    return parse_json(raw)

def judge_worker(gpu_id: int, pages: list, file_path: str, threshold: float):
    torch.cuda.set_device(gpu_id)
    print(f"GPU {gpu_id} starting\n{len(pages)} pages assigned")
    
    pipe = pipeline(
        "text-generation",
        model=JUDGE_MODEL,
        device=f"cuda:{gpu_id}"
    )
    
    kept = []
    dropped = []
    dropped_path = file_path.replace(".json", "_dropped.json")
    
    for i, page in enumerate(pages):
        score, reason = get_score(page["text"], pipe)
        page["score"] = score
        page["reason"] = reason
        if score >= threshold:
            kept.append(page)
            print(f"GPU {gpu_id}: [{i+1}/{len(pages)}] {score:.2f} KEPT: {page['title']}")
        else:
            dropped.append(page)
            print(f"GPU {gpu_id}: [{i+1}/{len(pages)}] {score:.2f} DROPPED: {page['title']}")
        
        # save every 200 pages
        if i % 200 == 0 and i > 0:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(kept, f, indent=2, ensure_ascii=False)
            with open(dropped_path, "w", encoding="utf-8") as f:
                json.dump(dropped, f, indent=2, ensure_ascii=False)
            print(f"\nGPU {gpu_id} saved {len(kept)} kept pages\n")
            torch.cuda.empty_cache()
                
    # final save
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
        
    with open(dropped_path, "w", encoding="utf-8") as f:
        json.dump(dropped, f, indent=2, ensure_ascii=False)

    print(f"\nGPU {gpu_id} done")
    
    

def load_pages(file_path: str) -> list:  # ← list not dict!
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
    
def combine_and_save(output_dir: str, num_gpus: int) -> None:
    all_kept = []
    all_dropped = []

    for gpu_id in range(num_gpus):
        kept_file = f"{output_dir}/filtered_gpu{gpu_id}.json"
        dropped_file = f"{output_dir}/filtered_gpu{gpu_id}_dropped.json"

        with open(kept_file, encoding="utf-8") as f:
            all_kept.extend(json.load(f))
        with open(dropped_file, encoding="utf-8") as f:
            all_dropped.extend(json.load(f))

    with open(f"{output_dir}/wsu_pages_clean.json", "w", encoding="utf-8") as f:
        json.dump(all_kept, f, indent=2, ensure_ascii=False)
    with open(f"{output_dir}/wsu_pages_dropped.json", "w", encoding="utf-8") as f:
        json.dump(all_dropped, f, indent=2, ensure_ascii=False)

             
def main():
    #just for hpc cluster                                                       
    os.environ['HF_HOME'] = os.path.expanduser('~/data/hf_cache')
    pages = load_pages(input_file)
    
    chunk_size = len(pages) // num_gpus
    chunks = []
    for i in range(num_gpus):
        start = i * chunk_size
        if i < num_gpus - 1:
            end = start + chunk_size
        else:
            end = len(pages)
        chunks.append(pages[start:end])
        print(f"GPU {i}: {len(chunks[i])} pages total")
    
    ctx = mp.get_context("spawn")
    processes = []
    for gpu_id in range(num_gpus):
        output_file = f"{output_dir}/filtered_gpu{gpu_id}.json"
        p = ctx.Process(target=judge_worker, args=(gpu_id, chunks[gpu_id], output_file, threshold))
        p.start()
        processes.append(p)
        print(f"GPU {gpu_id} start")
        
    for p in processes:
        p.join()
    print("DONE EVERYTHING")
    
    combine_and_save(output_dir, num_gpus)
    print("saved")
        

if __name__ == "__main__":
    main()
