"""
Personal Resume AI Assistant + Admin Upload
- Customer Mode: Anyone can chat (default)
- Admin Mode: Password-protected, can upload more docs
"""
import os
import streamlit as st
from rag_utility import process_document_to_chroma_db, answer_question

# ═══════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════
working_dir = os.path.dirname(os.path.abspath(__file__))
vectordb_path = os.path.join(working_dir, "doc_vectorstore")
resume_path = os.path.join(working_dir, "resume.pdf")
ADMIN_PASSWORD = "najeeb2026"  # Change to your own password

# ═══════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════
st.set_page_config(
    page_title="Ask About Najeeb",
    page_icon="🦙",
    layout="centered"
)

# ═══════════════════════════════════════
# AUTO-SETUP: Load resume on first run
# (Self-healing on cloud restart)
# ═══════════════════════════════════════
@st.cache_resource
def initialize_resume():
    """Auto-load resume.pdf into vector DB if not already loaded"""
    if not os.path.exists(vectordb_path):
        if not os.path.exists(resume_path):
            st.error("❌ resume.pdf not found in project folder!")
            st.stop()
        
        with st.spinner("🔄 Loading resume into vector database..."):
            process_document_to_chroma_db("resume.pdf")
        
        st.success("✅ Resume loaded successfully!")
    return True

# Initialize on app startup
initialize_resume()

# ═══════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ═══════════════════════════════════════
# SIDEBAR: Admin Login
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 Admin Access")
    
    if not st.session_state.admin_mode:
        password = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_mode = True
                st.success("✅ Admin mode activated")
                st.rerun()
            else:
                st.error("❌ Wrong password")
    else:
        st.success("👤 Admin Mode Active")
        if st.button("Logout"):
            st.session_state.admin_mode = False
            st.rerun()
    
    st.markdown("---")
    st.caption("💡 Visitors: just chat below")
    st.caption("🔑 Admin: enter password to upload docs")

# ═══════════════════════════════════════
# MAIN UI
# ═══════════════════════════════════════
st.title("🦙 Ask About Najeeb")
st.caption("Get to know Muhammed Najeeb — ask anything about his skills, projects, or experience!")

st.markdown("---")

# ═══════════════════════════════════════
# ADMIN ONLY: Upload Section
# ═══════════════════════════════════════
if st.session_state.admin_mode:
    st.markdown("### 📤 Upload Document (Admin Only)")

    
    uploaded_file = st.file_uploader(
        "Upload PDF (certificate, project doc, etc.)",
        type=["pdf"]
    )
    
    if uploaded_file is not None:
        save_path = os.path.join(working_dir, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner(f"Processing {uploaded_file.name}..."):
            process_document_to_chroma_db(uploaded_file.name)
        
        st.success(f"✅ {uploaded_file.name} added to knowledge base!")
    
    st.markdown("---")

# ═══════════════════════════════════════
# CHAT SECTION (Visible to Everyone)
# ═══════════════════════════════════════

# Suggested questions
with st.expander("💡 Try asking these questions"):
    st.markdown("""
    - What are Rebin's technical skills?
    - Tell me about his projects
    - Where did he study?
    - What is his work experience?
    - What programming languages does he know?
    - What are his career interests?
    - What AI projects has he built?
    """)

# Show chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(chat["question"])
    with st.chat_message("assistant"):
        st.markdown(chat["answer"])

# Chat input
user_question = st.chat_input("Ask anything about Rebin...")

if user_question:
    # Show user's question
    with st.chat_message("user"):
        st.markdown(user_question)
    
    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = answer_question(user_question)
        st.markdown(answer)
    
    # Save to history
    st.session_state.chat_history.append({
        "question": user_question,
        "answer": answer
    })

# Clear chat button
if st.session_state.chat_history:
    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()

# Footer
st.markdown("---")
st.caption("🚀 Built by Muhammed Najeeb | Powered by Llama 3.3 70B + RAG")