"""
One-time setup: Load resume.pdf into vector DB.
Run this ONCE before deploying the app.
"""
import os
from rag_utility import process_document_to_chroma_db

working_dir = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(working_dir, "resume.pdf")

# Check if resume exists
if not os.path.exists(resume_path):
    print("❌ resume.pdf not found!")
    print(f"📁 Please place resume.pdf in: {working_dir}")
    exit()

print("📄 Found resume.pdf")
print("🔄 Loading into vector database...\n")

# Process resume
process_document_to_chroma_db("resume.pdf")

print("✅ Resume loaded successfully!")
print("\n🚀 Now run: streamlit run app.py")