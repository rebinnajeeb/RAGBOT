"""
Personal Resume AI Assistant + Admin Upload
- Customer Mode: Anyone can chat (default)
- Admin Mode: Password-protected, can upload more docs (saved to GitHub = permanent)
"""
import os
import base64
import requests
from urllib.parse import quote
import streamlit as st
from rag_utility import process_document_to_chroma_db, answer_question


def _secret(key, default=None):
    """Read a value from Streamlit Secrets, falling back to a default."""
    try:
        return st.secrets[key]
    except Exception:
        return default


# ═══════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════
working_dir = os.path.dirname(os.path.abspath(__file__))
# Set ADMIN_PASSWORD in Streamlit Secrets (recommended, since the repo is public)
ADMIN_PASSWORD = _secret("ADMIN_PASSWORD", "najeeb2026")


def push_file_to_github(file_name, file_bytes):
    """Upload (or update) a file in the GitHub repo so it survives app restarts."""
    token = _secret("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set in Streamlit Secrets.")

    owner = _secret("GITHUB_OWNER", "rebinnajeeb")
    repo = _secret("GITHUB_REPO", "ragbot")
    branch = _secret("GITHUB_BRANCH", "main")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{quote(file_name)}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # If the file already exists, GitHub needs its current sha to overwrite it.
    sha = None
    existing = requests.get(api_url, headers=headers, params={"ref": branch}, timeout=30)
    if existing.status_code == 200:
        sha = existing.json().get("sha")

    payload = {
        "message": f"Add {file_name} via admin upload",
        "content": base64.b64encode(file_bytes).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(api_url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return True


# ═══════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════
st.set_page_config(
    page_title="Ask About Rebin",
    page_icon="🦙",
    layout="centered"
)

# ═══════════════════════════════════════
# AUTO-SETUP: Load every PDF on first run
# (Self-healing on cloud restart)
# ═══════════════════════════════════════
@st.cache_resource
def initialize_resume():
    """Load every PDF in the project folder (any filename) into the knowledge base."""
    pdf_files = [f for f in os.listdir(working_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        st.error("❌ No PDF found in the project folder!")
        st.stop()

    with st.spinner("🔄 Loading documents into knowledge base..."):
        for pdf in pdf_files:
            process_document_to_chroma_db(pdf)

    st.success(f"✅ Loaded {len(pdf_files)} document(s)!")
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
    st.info("📌 Uploaded PDFs are saved to your GitHub repo, so they stay permanently.")

    uploaded_file = st.file_uploader(
        "Upload PDF (certificate, project doc, etc.)",
        type=["pdf"]
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()

        # Save locally so it works immediately in this session
        save_path = os.path.join(working_dir, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        with st.spinner(f"Processing {uploaded_file.name}..."):
            process_document_to_chroma_db(uploaded_file.name)
        st.success(f"✅ {uploaded_file.name} added to the knowledge base!")

        # Push to GitHub so the document survives restarts (permanent)
        with st.spinner("💾 Saving to GitHub for permanent storage..."):
            try:
                push_file_to_github(uploaded_file.name, file_bytes)
                st.success("📌 Saved to GitHub — this document is now permanent!")
                st.caption("Streamlit will reboot in a moment to apply it.")
            except Exception as e:
                st.warning(
                    f"⚠️ Added for this session, but couldn't save to GitHub "
                    f"permanently: {e}"
                )

    st.markdown("---")

# ═══════════════════════════════════════
# CHAT SECTION (Visible to Everyone)
# ═══════════════════════════════════════

# Suggested questions
with st.expander("💡 Try asking these questions"):
    st.markdown("""
    - What are Najeeb's technical skills?
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
user_question = st.chat_input("Ask anything about Najeeb...")

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
