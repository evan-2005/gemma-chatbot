import os
import glob
import pandas as pd
import fitz  # PyMuPDF
import subprocess

# -------- SETTINGS --------
LOCAL_DIR = "./data"              # your local directory
OUTPUT_FILE = "combined_text_output.txt"
MODEL_NAME = "llama3.2"           # any local Ollama model
CHUNK_SIZE = 20000                # chars per prompt chunk
# ---------------------------

def extract_txt(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df.to_string(index=False)
    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}")
        return ""

def extract_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text")
    except Exception as e:
        print(f"[WARN] Could not extract from {file_path}: {e}")
    return text

def collect_texts(folder):
    all_texts = []
    patterns = ["*.txt", "*.csv", "*.pdf"]
    for pattern in patterns:
        for file_path in glob.glob(os.path.join(folder, pattern)):
            print(f"[INFO] Extracting from {file_path}")
            if file_path.endswith(".txt"):
                text = extract_txt(file_path)
            elif file_path.endswith(".csv"):
                text = extract_csv(file_path)
            elif file_path.endswith(".pdf"):
                text = extract_pdf(file_path)
            else:
                continue
            if text.strip():
                header = f"\n\n===== FILE: {os.path.basename(file_path)} =====\n\n"
                all_texts.append(header + text)
    return "\n".join(all_texts)

def run_ollama(prompt, model=MODEL_NAME):
    """Run prompt on local Ollama and return response."""
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def main():
    # Step 1: Extract and combine text
    combined_text = collect_texts(LOCAL_DIR)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(combined_text)
    print(f"[INFO] Combined file saved: {OUTPUT_FILE}")

    # Step 2: Summarize in chunks
    summaries = []
    for i in range(0, len(combined_text), CHUNK_SIZE):
        chunk = combined_text[i:i + CHUNK_SIZE]
        prompt = f"Summarize this document chunk ({i//CHUNK_SIZE + 1}):\n\n{chunk}"
        print(f"[INFO] Sending chunk {i//CHUNK_SIZE + 1} to Ollama...")
        summary = run_ollama(prompt)
        summaries.append(summary)

    # Step 3: Combine summaries
    print("[INFO] Combining all summaries...")
    final_prompt = "Combine the following summaries into one cohesive summary:\n\n" + "\n\n".join(summaries)
    final_summary = run_ollama(final_prompt)

    with open("final_summary.txt", "w", encoding="utf-8") as f:
        f.write(final_summary)
    print("✅ Done! Final summary saved to: final_summary.txt")

if __name__ == "__main__":
    main()
