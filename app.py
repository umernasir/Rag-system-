import html

import requests
import streamlit as st

# =========================================================
# CONFIG
# =========================================================

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RAG System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SAMPLE_QUESTIONS = [
    "What is the purpose of Government AI Cloud?",
    "Summarize the key points of the uploaded documents.",
    "Which policies or deadlines are mentioned?",
]

# =========================================================
# SESSION STATE
# =========================================================

for key, default in {
    "token": None,
    "username": None,
    "last_answer": None,
    "last_question": None,
    "history": [],
    "question_input": "",
    "new_conversation":False,
    "upload_message": None,
    "upload_error": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&display=swap');

    :root {
        --ink: #0f172a;
        --muted: #475569;
        --pine: #1e40af;
        --pine-deep: #0b1b3f;
        --mist: #f1f5f9;
        --line: #e2e8f0;
        --brass: #0ea5e9;
        --signal: #16a34a;
        --serif: 'Source Serif 4', Georgia, serif;
        --sans: 'IBM Plex Sans', system-ui, sans-serif;
    }

    html, body, .stApp, [class*="css"] {
        font-family: var(--sans);
        color: var(--ink);
    }

    .stApp { background: var(--mist); }

    .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; }

    [data-testid="stSidebar"] {
        background: var(--pine-deep);
        border-right: 1px solid #1e3a8a;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] h3 {
        font-family: var(--serif);
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: .25rem;
    }
    [data-testid="stSidebar"] hr { border-color: #24408a; }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        background: transparent;
        color: #f1f5f9;
        border: 1px solid #35509a;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #16307a;
        border-color: var(--brass);
        color: #fff;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: #12275f;
        border: 1px dashed #4a66b8;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
        color: #dbe4f5 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        background: #1d3a8f;
        border: 1px solid #4a66b8;
        color: #fff !important;
    }

    .brand { display: flex; align-items: center; gap: 12px; margin: 4px 0 22px; }
    .brand-mark {
        width: 40px; height: 40px; border-radius: 8px;
        background: var(--brass);
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
    }
    .brand-title {
        font-family: var(--serif); font-size: 17px; font-weight: 600;
        color: #fff; line-height: 1.2;
    }
    .brand-sub { font-size: 12px; color: #9fb3d9; }

    .profile {
        display: flex; align-items: center; gap: 10px;
        padding: 12px 14px; margin-bottom: 22px;
        background: #12275f; border: 1px solid #26438f; border-radius: 8px;
    }
    .avatar {
        width: 32px; height: 32px; border-radius: 50%;
        background: #2563eb; color: #fff; font-weight: 600; font-size: 14px;
        display: flex; align-items: center; justify-content: center;
    }
    .profile-name { color: #fff; font-weight: 600; font-size: 14px; }
    .profile-status { color: #86efac; font-size: 12px; }

    .masthead {
        background: var(--pine);
        border-bottom: 3px solid var(--brass);
        border-radius: 10px 10px 0 0;
        padding: 34px 40px 30px;
        display: flex; justify-content: space-between; align-items: flex-start;
        gap: 24px; flex-wrap: wrap;
    }
    .masthead h1 {
        font-family: var(--serif);
        font-size: 36px; font-weight: 600; letter-spacing: -0.3px;
        color: #fff; margin: 0 0 10px; padding: 0; line-height: 1.15;
    }
    .masthead p {
        color: #cbd8f2; font-size: 15px; line-height: 1.65;
        max-width: 640px; margin: 0;
    }
    .status-pill {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 6px 14px; border-radius: 999px;
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.18);
        color: #eef3fb; font-size: 13px; white-space: nowrap;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .dot.on  { background: #4ade80; box-shadow: 0 0 0 3px rgba(74,222,128,.22); }
    .dot.off { background: #f87171; box-shadow: 0 0 0 3px rgba(248,113,113,.22); }

    .stat-strip {
        display: flex; flex-wrap: wrap;
        background: #fff;
        border: 1px solid var(--line); border-top: none;
        border-radius: 0 0 10px 10px;
        margin-bottom: 26px;
    }
    .stat {
        flex: 1 1 180px; padding: 20px 28px;
        border-right: 1px solid var(--line);
    }
    .stat:last-child { border-right: none; }
    .stat-label { color: var(--muted); font-size: 13px; margin-bottom: 4px; }
    .stat-value {
        font-family: var(--serif); font-size: 30px; font-weight: 600;
        color: var(--ink); line-height: 1.1;
    }
    .stat-value.ok { color: var(--signal); }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
    .stTabs [data-baseweb="tab"] {
        height: 46px; padding: 0 18px;
        font-weight: 500; color: var(--muted);
    }
    .stTabs [aria-selected="true"] { color: var(--pine) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background: var(--brass); height: 3px; }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.panel-marker) {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 10px 14px;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.answer-marker) {
        border-left: 4px solid var(--brass);
    }

    .panel-title {
        font-family: var(--serif); font-size: 21px; font-weight: 600;
        color: var(--ink); margin: 4px 0 2px;
    }
    .panel-desc { color: var(--muted); font-size: 14px; margin-bottom: 6px; }

    .answer-meta {
        color: var(--muted); font-size: 13px; margin-bottom: 4px;
    }
    .answer-question {
        font-family: var(--serif); font-size: 20px; font-weight: 600;
        color: var(--ink); margin-bottom: 14px; line-height: 1.35;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.answer-marker) .stMarkdown p,
    [data-testid="stVerticalBlockBorderWrapper"]:has(.answer-marker) .stMarkdown li {
        font-family: var(--serif);
        font-size: 17px; line-height: 1.75; color: #1e293b;
    }

    .stTextArea textarea, .stTextInput input {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        background: #fff;
        font-family: var(--sans);
        font-size: 15px;
        color: var(--ink);
        -webkit-text-fill-color: var(--ink);
    }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #94a3b8; -webkit-text-fill-color: #94a3b8;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--pine);
        box-shadow: 0 0 0 1px var(--pine);
    }

    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        border-radius: 8px; min-height: 44px; font-weight: 600;
        transition: background .15s, border-color .15s;
    }
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background: var(--pine); border: 1px solid var(--pine); color: #fff;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--pine-deep); border-color: var(--pine-deep); color: #fff;
    }
    .stButton > button[kind="secondary"] {
        background: #fff; color: var(--pine); border: 1px solid #c3cfdf;
        font-weight: 500; font-size: 13px; min-height: 38px;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--brass); color: var(--ink); background: #eff6ff;
    }
    .stButton > button:focus-visible { outline: 2px solid var(--brass); outline-offset: 2px; }

    [data-testid="stMetric"] {
        background: var(--mist); border: 1px solid var(--line);
        border-radius: 8px; padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] p { color: var(--muted); font-size: 13px; }
    [data-testid="stMetricValue"] { font-family: var(--serif); font-size: 26px; color: var(--ink); }

    .doc-row {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 4px; border-bottom: 1px solid var(--line);
    }
    .doc-row:last-child { border-bottom: none; }
    .doc-icon {
        width: 38px; height: 44px; border-radius: 4px;
        background: #fbeeee; border: 1px solid #efc9c9; color: #b42318;
        font-size: 10px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
    }
    .doc-name { font-weight: 500; font-size: 14.5px; color: var(--ink); word-break: break-all; }
    .doc-sub { font-size: 12.5px; color: var(--muted); }

    .empty {
        text-align: center; padding: 38px 10px; color: var(--muted); font-size: 14.5px;
    }
    .empty b { display: block; font-family: var(--serif); font-size: 18px; color: var(--ink); margin-bottom: 4px; }

    .login-head { text-align: center; margin: 56px 0 24px; }
    .login-mark {
        width: 64px; height: 64px; border-radius: 12px; margin: 0 auto 18px;
        background: var(--pine); border-bottom: 3px solid var(--brass);
        display: flex; align-items: center; justify-content: center; font-size: 30px;
    }
    .login-title {
        font-family: var(--serif); font-size: 34px; font-weight: 600;
        color: var(--ink); letter-spacing: -0.3px;
    }
    .login-sub { color: var(--muted); font-size: 15px; margin-top: 6px; }

    [data-testid="stForm"] {
        background: #fff; border: 1px solid var(--line);
        border-radius: 12px; padding: 26px 26px 20px;
        box-shadow: 0 10px 30px rgba(15,23,42,.08);
    }

    .footer {
        text-align: center; color: #94a3b8; font-size: 12.5px; padding: 34px 0 6px;
    }

    @media (max-width: 720px) {
        .masthead { padding: 26px 22px; }
        .masthead h1 { font-size: 28px; }
        .stat { border-right: none; border-bottom: 1px solid var(--line); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# API HELPERS
# =========================================================


def sign_out():
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.last_answer = None
    st.session_state.last_question = None
    st.session_state.history = []


def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def check_auth(response):
    if response is not None and response.status_code == 401:
        sign_out()
        st.rerun()
    return response


def login(username, password):
    try:
        response = requests.post(
            f"{API_URL}/login",
            data={"username": username, "password": password},
            timeout=30,
        )
        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.session_state.username = username
            return True, None
        return False, "Incorrect username or password."
    except requests.RequestException:
        return False, "Can't reach the server. Check that the backend is running."


def upload_document(files):
    multipart_files = [
        ("files", (file.name, file.getvalue(), "application/pdf"))
        for file in files
    ]
    return check_auth(
        requests.post(
            f"{API_URL}/upload",
            headers=headers(),
            files=multipart_files,
            timeout=300,
        )
    )


def ask_question(question):
    return check_auth(
        requests.post(
            f"{API_URL}/ask",
            headers=headers(),
            json={"question": question},
            timeout=300,
        )
    )


def fetch_stats():
    try:
        response = check_auth(
            requests.get(f"{API_URL}/stats", headers=headers(), timeout=10)
        )
        if response.status_code == 200:
            return True, response.json()
        return True, None
    except requests.RequestException:
        return False, None


def fetch_documents():
    try:
        response = check_auth(
            requests.get(f"{API_URL}/documents", headers=headers(), timeout=15)
        )
        if response.status_code == 200:
            return response.json().get("documents", [])
    except requests.RequestException:
        return None
    return []


def use_sample(text):
    st.session_state.question_input = text


# =========================================================
# LOGIN PAGE
# =========================================================

if st.session_state.token is None:

    st.markdown(
        """
        <div class="login-head">
        <div class="login-mark">🏛️</div>
        <div class="login-title">RAG Assistant</div>
        <div class="login-sub">Sign in to search and question your document library.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.4, 1])

    with center:
        with st.form("login_form"):
            st.markdown(
                '<div class="panel-title">Sign in</div>',
                unsafe_allow_html=True,
            )
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )
            submitted = st.form_submit_button(
                "Sign in", type="primary", use_container_width=True
            )

        if submitted:
            if not username or not password:
                st.warning("Enter your username and password.")
            else:
                with st.spinner("Signing in…"):
                    ok, error = login(username, password)
                if ok:
                    st.rerun()
                else:
                    st.error(error)

        st.caption("Demo account: admin / admin123")

    st.markdown(
        '<div class="footer">Secure sign-in · Agentic RAG · Government AI Cloud</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# DASHBOARD
# =========================================================

else:
    online, stats = fetch_stats()
    safe_name = html.escape(st.session_state.username or "")
    initial = html.escape((st.session_state.username or "?")[:1].upper())

    # ---------------- SIDEBAR ----------------

    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-mark">🏛️</div>
                <div>
                    <div class="brand-title">Rag Assistant</div>
                    <div class="brand-sub">Cloud console</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="profile">
                <div class="avatar">{initial}</div>
                <div>
                    <div class="profile-name">{safe_name}</div>
                    <div class="profile-status">● Signed in</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        # ---- Upload action (inside sidebar) ----
        if uploaded_files:
            st.caption(
                f"{len(uploaded_files)} file"
                f"{'s' if len(uploaded_files) != 1 else ''} selected"
            )

            if st.button("Add to knowledge base", use_container_width=True):
                with st.spinner("Indexing documents…"):
                    try:
                        response = upload_document(uploaded_files)
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.upload_message = (
                                f"Document indexed. "
                                f"{data.get('documents', '–')} documents · "
                                f"{data.get('chunks', '–')} chunks"
                            )
                            st.session_state.upload_error = None
                        else:
                            try:
                                message = response.json().get(
                                    "detail", "Upload failed."
                                )
                            except Exception:
                                message = "Upload failed."
                            st.session_state.upload_error = message
                            st.session_state.upload_message = None
                    except requests.RequestException:
                        st.session_state.upload_error = (
                            "Can't reach the server. Try again shortly."
                        )
                        st.session_state.upload_message = None
                st.rerun()

        # ---- Persisted upload status ----
        if st.session_state.get("upload_message"):
            st.success(st.session_state.upload_message)
            st.session_state.upload_message = None

        if st.session_state.get("upload_error"):
            st.error(st.session_state.upload_error)
            st.session_state.upload_error = None

        st.divider()

        if st.button("Refresh", use_container_width=True):
            st.rerun()

        if st.button("Sign out", use_container_width=True):
            sign_out()
            st.rerun()

    # ---------------- MASTHEAD ----------------

    pill = (
        '<span class="dot on"></span> Systems operational'
        if online
        else '<span class="dot off"></span> Backend unreachable'
    )

    st.markdown(
        f"""
        <div class="masthead">
            <div>
                <h1>Document intelligence</h1>
                <p>Ask questions in plain language and get answers drawn from the
                government documents in your knowledge base.</p>
            </div>
            <div class="status-pill">{pill}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- STAT STRIP ----------------

    if stats and stats.get("indexed"):
        st.markdown(
            f"""
            <div class="stat-strip">
                <div class="stat"><div class="stat-label">Documents</div>
                    <div class="stat-value">{html.escape(str(stats.get("documents", 0)))}</div></div>
                <div class="stat"><div class="stat-label">Searchable passages</div>
                    <div class="stat-value">{html.escape(str(stats.get("chunks", 0)))}</div></div>
                <div class="stat"><div class="stat-label">Passages per answer</div>
                    <div class="stat-value">{html.escape(str(stats.get("top_k", "–")))}</div></div>
                <div class="stat"><div class="stat-label">Status</div>
                    <div class="stat-value ok">Ready</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="stat-strip">
                <div class="stat" style="flex-basis:100%">
                    <div class="stat-label">Knowledge base</div>
                    <div class="stat-value" style="font-size:20px">
                        Empty. Upload a PDF from the sidebar to get started.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------------- TABS ----------------

    tab_ask, tab_docs = st.tabs(["Ask a question", "Knowledge base"])

    # ===== ASK =====
    with tab_ask:
        with st.container(border=True):
            st.markdown(
                """
                <span class="panel-marker"></span>
                <div class="panel-title">Ask your documents</div>
                <div class="panel-desc">Answers are based only on documents you've added.</div>
                """,
                unsafe_allow_html=True,
            )
            if st.session_state.new_conversation:
               st.session_state.question_input = ""
               st.session_state.new_conversation = False

            question = st.text_area(
                "Question",
                key="question_input",
                placeholder="e.g. What is the purpose of Government AI Cloud?",
                height=110,
                label_visibility="collapsed",
            )

            chip_cols = st.columns(len(SAMPLE_QUESTIONS))
            for col, sample in zip(chip_cols, SAMPLE_QUESTIONS):
                col.button(
                    sample,
                    key=f"sample_{sample}",
                    on_click=use_sample,
                    args=(sample,),
                    use_container_width=True,
                )

            ask_clicked = st.button(
            "Get answer", type="primary", use_container_width=True
        )

        if st.button(
            "New conversation",
            key="new_conversation_button",
            use_container_width=True,
        ):
            response = check_auth(
                requests.delete(
                    f"{API_URL}/conversation",
                    headers=headers(),
                    timeout=10,
                )
            )

            if response.status_code == 200:
                st.session_state.last_answer = None
                st.session_state.last_question = None
                st.session_state.new_conversation = True
                st.rerun()
            else:
                st.error("Could not clear the conversation.")
    if ask_clicked:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Searching documents and preparing an answer…"):
                try:
                    response = ask_question(question)

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.last_question = question
                        st.session_state.last_answer = data
                        st.session_state.history.insert(
                            0, {"question": question, "data": data}
                        )
                        st.session_state.history = st.session_state.history[:10]

                    else:
                        try:
                            message = response.json().get(
                                "detail", "Something went wrong. Try again."
                            )
                        except Exception:
                            message = "Something went wrong. Try again."

                        st.error(message)

                except requests.RequestException:
                    st.error("Can't reach the server. Try again shortly.")
    if st.session_state.last_answer:
            answer_data = st.session_state.last_answer

            st.write("")
            with st.container(border=True):
                st.markdown(
                    f"""
                    <span class="panel-marker"></span><span class="answer-marker"></span>
                    <div class="answer-meta">Answer</div>
                    <div class="answer-question">{html.escape(st.session_state.last_question or "")}</div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(answer_data.get("answer", ""))
                sources = answer_data.get("sources", [])

                if sources:
                    st.markdown(
                        """
                        <div style="
                            margin-top: 20px;
                            padding-top: 14px;
                            border-top: 1px solid #e2e8f0;
                            font-weight: 600;
                            font-size: 15px;
                            color: #0f172a;
                        ">
                            Sources
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    for source in sources:
                        source_name = html.escape(
                            str(source.get("source", "Unknown document"))
                        )
                        page = html.escape(
                            str(source.get("page", "?"))
                        )

                        st.markdown(
                            f"""
                            <div style="
                                margin-top: 8px;
                                padding: 10px 12px;
                                background: #f8fafc;
                                border: 1px solid #e2e8f0;
                                border-radius: 6px;
                                color: #334155;
                                font-size: 14px;
                            ">
                                📄 {source_name}
                                &nbsp;·&nbsp;
                                Page {page}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            

            st.write("")
            m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
            m1.metric("Search attempts", answer_data.get("attempts", "–"))
            m2.metric("Passages used", answer_data.get("documents_retrieved", "–"))
            m3.metric("Result", "Successful")
            with m4:
                st.write("")
                st.download_button(
                    "Download answer",
                    data=(
                        f"Question:\n{st.session_state.last_question}\n\n"
                        f"Answer:\n{answer_data.get('answer', '')}\n"
                    ),
                    file_name="answer.txt",
                    use_container_width=True,
                )

    st.write("")
    with st.expander("Recent questions", expanded=True):
            if st.session_state.history:
                for item in st.session_state.history:
                   st.markdown(f"**{item['question']}**")
                   st.write(item["data"].get("answer", ""))
                st.divider()
            else:
                st.caption("No recent questions yet.")

    # ===== DOCUMENTS =====
    with tab_docs:
        with st.container(border=True):
            st.markdown(
                """
                <span class="panel-marker"></span>
                <div class="panel-title">Indexed documents</div>
                <div class="panel-desc">These documents are available to the assistant.</div>
                """,
                unsafe_allow_html=True,
            )

            documents = fetch_documents()

            if documents is None:
                st.error("Can't load documents. The backend isn't reachable.")
            elif not documents:
                st.markdown(
                    """
                    <div class="empty">
                        <b>No documents yet</b>
                        Upload a PDF from the sidebar to build your knowledge base.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                rows = ""
                for document in documents:
                    source = html.escape(str(document.get("source", "Unknown document")))
                    rows += f"""
                    <div class="doc-row">
                        <div class="doc-icon">PDF</div>
                        <div>
                            <div class="doc-name">{source}</div>
                            <div class="doc-sub">Indexed and searchable</div>
                        </div>
                    </div>
                    """
                st.markdown(rows, unsafe_allow_html=True)

    st.markdown(
        '<div class="footer">Government AI Cloud · Agentic RAG · Secure AI infrastructure</div>',
        unsafe_allow_html=True,
    )