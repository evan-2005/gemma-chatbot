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
    """Extract text from a .txt file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_csv(file_path):
    """Extract text from a .csv file by converting to string."""
    try:
        df = pd.read_csv(file_path)
        return df.to_string(index=False)
    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}")
        return ""

def extract_pdf(file_path):
    """Extract text from a .pdf file using PyMuPDF."""
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text")
    except Exception as e:
        print(f"[WARN] Could not extract from {file_path}: {e}")
    return text

def collect_texts(folder):
    """
    Collect and combine text from all .txt, .csv, and .pdf files in a folder.
    
    Args:
        folder: Path to the folder containing documents
        
    Returns:
        Combined text from all documents
    """
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
    """
    Run a prompt on local Ollama and return the response.
    
    Args:
        prompt: The text prompt to send to Ollama
        model: The Ollama model to use (default: llama3.2)
        
    Returns:
        The model's response as a string
    """
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def main():
    """
    Main function to:
    1. Extract and combine text from documents
    2. Summarize in chunks using Ollama
    3. Create a final combined summary
    """
    # Step 1: Extract and combine text
    print("[INFO] Starting document extraction...")
    combined_text = collect_texts(LOCAL_DIR)
    
    if not combined_text.strip():
        print("[ERROR] No text extracted from documents. Check your data folder.")
        return
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(combined_text)
    print(f"[INFO] Combined file saved: {OUTPUT_FILE}")
    print(f"[INFO] Total characters: {len(combined_text)}")

    # Step 2: Summarize in chunks
    print(f"[INFO] Processing {len(combined_text) // CHUNK_SIZE + 1} chunks...")
    summaries = []
    
    for i in range(0, len(combined_text), CHUNK_SIZE):
        chunk_num = i // CHUNK_SIZE + 1
        chunk = combined_text[i:i + CHUNK_SIZE]
        prompt = f"Summarize this document chunk ({chunk_num}):\n\n{chunk}"
        
        print(f"[INFO] Sending chunk {chunk_num} to Ollama ({MODEL_NAME})...")
        summary = run_ollama(prompt)
        summaries.append(f"=== Chunk {chunk_num} Summary ===\n{summary}")
        
        # Save intermediate summaries
        with open(f"chunk_{chunk_num}_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)

    # Step 3: Combine summaries
    print("[INFO] Combining all summaries...")
    final_prompt = (
        "Combine the following summaries into one cohesive final summary:\n\n"
        + "\n\n".join(summaries)
    )
    final_summary = run_ollama(final_prompt)

    with open("final_summary.txt", "w", encoding="utf-8") as f:
        f.write(final_summary)
    
    print("✅ Done! Final summary saved to: final_summary.txt")
    print(f"✅ Processed {len(summaries)} chunks")

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)
        print(f"[INFO] Created directory: {LOCAL_DIR}")
        print(f"[INFO] Please add your .txt, .csv, or .pdf files to {LOCAL_DIR}")
    else:
        main()
