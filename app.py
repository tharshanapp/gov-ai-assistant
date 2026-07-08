"""
Government Regulatory AI Assistant
Streamlit + LlamaIndex + Ollama (free) or OpenAI
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging (console only — never shown to end users)
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_SOURCE_DIR = BASE_DIR / "data_source"
INDEX_CACHE_DIR = BASE_DIR / ".index_cache"
PERSIST_DIR = INDEX_CACHE_DIR / "storage"
FINGERPRINT_FILE = INDEX_CACHE_DIR / "corpus.fp"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

SYSTEM_PROMPT = """You are an elite legal and regulatory compliance assistant for public sector officers.

When answering queries based on the provided documents, you must:
1. Provide accurate, concise answers grounded ONLY in the supplied context.
2. Use formal, professional language suitable for government correspondence.
3. Strictly extract and format your source citations at the TOP of your response inside a clearly marked block.

Citation format (one line per source used):
🏛️ Organization: [Name] | 📅 Year: [YYYY] | 📜 Reference Section: [Section/Paragraph]

If Organization, Year, or Section/Paragraph cannot be determined from the text, write
"Not explicitly mentioned in text" for that field.

After the citation block, provide your detailed answer. If the context does not contain
enough information, state that clearly and do not invent citations or legal references."""

GOVERNMENT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {
    --gov-navy: #1A2B4A;
    --gov-navy-light: #2C4A7C;
    --gov-gold: #C9A227;
    --gov-gold-light: #E8C547;
    --gov-cream: #F8F9FB;
    --gov-border: #D4DCE8;
}

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
}

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 920px;
}

/* Hero header */
.gov-header {
    background: linear-gradient(135deg, var(--gov-navy) 0%, var(--gov-navy-light) 100%);
    border-left: 6px solid var(--gov-gold);
    border-radius: 0 12px 12px 0;
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(26, 43, 74, 0.15);
}
.gov-header h1 {
    font-family: 'Source Serif 4', serif;
    color: #FFFFFF !important;
    font-size: 1.85rem;
    font-weight: 700;
    margin: 0 0 0.35rem 0;
    letter-spacing: 0.02em;
}
.gov-header p {
    color: rgba(255, 255, 255, 0.88);
    margin: 0;
    font-size: 1rem;
}

/* Status badges */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.status-ok {
    background: #E6F4EA;
    color: #1B5E20;
    border: 1px solid #A5D6A7;
}
.status-warn {
    background: #FFF8E1;
    color: #E65100;
    border: 1px solid #FFE082;
}
.status-error {
    background: #FFEBEE;
    color: #B71C1C;
    border: 1px solid #EF9A9A;
}

/* Citation callout */
.citation-box {
    background: linear-gradient(to right, #FFFDF5, #FFFBEB);
    border: 1px solid var(--gov-gold);
    border-left: 5px solid var(--gov-gold);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0 1rem 0;
    font-size: 0.92rem;
    line-height: 1.6;
    color: var(--gov-navy);
}
.citation-box strong {
    color: var(--gov-navy);
}

/* Chat bubbles */
.stChatMessage {
    border-radius: 12px !important;
    border: 1px solid var(--gov-border) !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F0F4FA 0%, #E8EDF5 100%);
    border-right: 1px solid var(--gov-border);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

.sidebar-title {
    font-family: 'Source Serif 4', serif;
    color: var(--gov-navy);
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 2px solid var(--gov-gold);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Hide Streamlit branding footer on Community Cloud */
footer { visibility: hidden; }
</style>
"""


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------
def _get_secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then environment variables."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError, TypeError):
        return os.getenv(key, default)


def get_config() -> dict[str, str]:
    provider = _get_secret("AI_PROVIDER", "ollama").lower().strip()
    return {
        "provider": provider,
        "openai_api_key": _get_secret("OPENAI_API_KEY"),
        "openai_model": _get_secret("OPENAI_MODEL", "gpt-4o-mini"),
        "embed_model": _get_secret("EMBED_MODEL", "text-embedding-3-small"),
        "ollama_model": _get_secret("OLLAMA_MODEL", "llama3.2"),
        "ollama_embed_model": _get_secret("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        "ollama_base_url": _get_secret("OLLAMA_BASE_URL", "http://localhost:11434"),
        "admin_password": _get_secret("ADMIN_PASSWORD", "admin123"),
    }


def is_ai_ready(config: dict[str, str]) -> bool:
    if config["provider"] == "openai":
        return bool(config["openai_api_key"])
    return ollama_is_running(config["ollama_base_url"])


def ollama_is_running(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def configure_llama_settings(config: dict[str, str]) -> None:
    from llama_index.core import Settings
    from llama_index.core.node_parser import SentenceSplitter

    Settings.node_parser = SentenceSplitter(chunk_size=2048, chunk_overlap=100)

    if config["provider"] == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI

        Settings.llm = OpenAI(model=config["openai_model"], api_key=config["openai_api_key"])
        Settings.embed_model = OpenAIEmbedding(
            model=config["embed_model"],
            api_key=config["openai_api_key"],
            embed_batch_size=8,
        )
    else:
        from llama_index.embeddings.ollama import OllamaEmbedding
        from llama_index.llms.ollama import Ollama

        Settings.llm = Ollama(
            model=config["ollama_model"],
            base_url=config["ollama_base_url"],
            request_timeout=300.0,
        )
        Settings.embed_model = OllamaEmbedding(
            model_name=config["ollama_embed_model"],
            base_url=config["ollama_base_url"],
        )


def model_cache_key(config: dict[str, str]) -> str:
    if config["provider"] == "openai":
        return f"openai:{config['openai_model']}:{config['embed_model']}"
    return f"ollama:{config['ollama_model']}:{config['ollama_embed_model']}"


# ---------------------------------------------------------------------------
# Metadata extraction from filenames & content
# ---------------------------------------------------------------------------
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
SECTION_PATTERN = re.compile(
    r"(?:section|sec\.?|paragraph|para\.?|clause|article|reg\.?)\s*[\d\.ivxlcdm\-]+",
    re.IGNORECASE,
)
ORG_KEYWORDS = [
    "ministry", "department", "commission", "authority", "council",
    "bureau", "office", "agency", "government", "public service",
    "treasury", "finance", "health", "education", "defence", "defense",
]


def _guess_organization(filename: str, text_sample: str = "") -> str:
    combined = f"{filename} {text_sample[:2000]}".lower()
    for keyword in ORG_KEYWORDS:
        match = re.search(
            rf"([\w\s\-&']+{keyword}[\w\s\-&']*)",
            combined,
            re.IGNORECASE,
        )
        if match:
            org = match.group(1).strip(" -_")
            return org.title()[:120]
    stem = Path(filename).stem.replace("_", " ").replace("-", " ")
    return stem.title()[:120] if stem else "Government Authority"


def _guess_year(filename: str, text_sample: str = "") -> str:
    for source in (filename, text_sample[:1500]):
        match = YEAR_PATTERN.search(source)
        if match:
            return match.group(0)
    return "Not explicitly mentioned in text"


def _extract_sections(text: str) -> list[str]:
    return list(dict.fromkeys(m.group(0) for m in SECTION_PATTERN.finditer(text[:8000])))[:5]


def build_document_metadata(filename: str, text: str) -> dict[str, str]:
    sections = _extract_sections(text)
    return {
        "filename": filename,
        "organization": _guess_organization(filename, text),
        "year": _guess_year(filename, text),
        "reference_section": sections[0] if sections else "Not explicitly mentioned in text",
        "source_path": str(DATA_SOURCE_DIR / filename),
    }


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------
def scan_data_source() -> list[Path]:
    if not DATA_SOURCE_DIR.exists():
        DATA_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        return []
    files: list[Path] = []
    for path in sorted(DATA_SOURCE_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def _read_pdf(path: Path) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        if not pages:
            return "", "No extractable text (possibly scanned/image PDF)."
        return "\n\n".join(pages), None
    except Exception as exc:
        logger.exception("Failed to read PDF: %s", path.name)
        return "", str(exc)


def _read_docx(path: Path) -> tuple[str, str | None]:
    try:
        from docx import Document

        doc = Document(str(path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            return "", "Document contains no readable paragraphs."
        return "\n\n".join(paragraphs), None
    except Exception as exc:
        logger.exception("Failed to read DOCX: %s", path.name)
        return "", str(exc)


def _read_plaintext(path: Path) -> tuple[str, str | None]:
    try:
        return path.read_text(encoding="utf-8", errors="replace"), None
    except Exception as exc:
        logger.exception("Failed to read text file: %s", path.name)
        return "", str(exc)


def load_single_document(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text, err = _read_pdf(path)
    elif suffix in {".docx", ".doc"}:
        if suffix == ".doc":
            return None, "Legacy .doc format is not supported; please convert to .docx or .pdf."
        text, err = _read_docx(path)
    else:
        text, err = _read_plaintext(path)

    if err:
        return None, err
    if not text.strip():
        return None, "File is empty or unreadable."

    metadata = build_document_metadata(path.name, text)
    return {"text": text, "metadata": metadata}, None


def compute_corpus_fingerprint(files: list[Path]) -> str:
    hasher = hashlib.sha256()
    for path in files:
        stat = path.stat()
        hasher.update(f"{path.name}:{stat.st_size}:{stat.st_mtime}".encode())
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# LlamaIndex RAG engine (in-memory vector store — no C++ build tools needed)
# ---------------------------------------------------------------------------
def load_all_documents(files: list[Path]) -> tuple[list, list[str]]:
    from llama_index.core import Document

    documents: list[Document] = []
    errors: list[str] = []

    for path in files:
        payload, err = load_single_document(path)
        if err:
            errors.append(f"{path.name}: {err}")
            continue
        meta = payload["metadata"]
        documents.append(
            Document(
                text=payload["text"],
                metadata={
                    "filename": meta["filename"],
                    "organization": meta["organization"],
                    "year": meta["year"],
                    "reference_section": meta["reference_section"],
                },
            )
        )
    return documents, errors


def _is_rate_limit_error(exc: Exception) -> bool:
    name = type(exc).__name__
    if name in {"RateLimitError", "RateLimitReached", "InsufficientQuotaError"}:
        return True
    msg = str(exc).lower()
    return "rate limit" in msg or "429" in msg or "quota" in msg


def build_index_resilient(documents: list, use_openai: bool) -> Any:
    """Build vector index; retries only needed for OpenAI rate limits."""
    from llama_index.core import VectorStoreIndex

    if not use_openai:
        if len(documents) == 1:
            return VectorStoreIndex.from_documents(documents)
        index = VectorStoreIndex.from_documents([documents[0]])
        for doc in documents[1:]:
            index.insert(doc)
        return index

    last_err: Exception | None = None
    for attempt in range(15):
        try:
            if len(documents) == 1:
                return VectorStoreIndex.from_documents(documents)
            index = VectorStoreIndex.from_documents([documents[0]])
            for doc in documents[1:]:
                time.sleep(5)
                index.insert(doc)
            return index
        except Exception as exc:
            if not _is_rate_limit_error(exc):
                raise
            last_err = exc
            wait = min(120, 15 * (attempt + 1))
            logger.warning("OpenAI rate limit — waiting %ds (attempt %d/15)", wait, attempt + 1)
            time.sleep(wait)

    raise last_err or RuntimeError("Indexing failed after repeated rate limits.")


@st.cache_resource(show_spinner=False)
def get_vector_index(model_key: str, corpus_fingerprint: str, config_snapshot: tuple):
    """Build or load a persisted vector index."""
    from llama_index.core import StorageContext, load_index_from_storage

    config = dict(config_snapshot)
    configure_llama_settings(config)

    INDEX_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    files = scan_data_source()
    if not files:
        return None, [], []

    cache_fp = f"{corpus_fingerprint}:{model_key}"
    if (
        FINGERPRINT_FILE.exists()
        and PERSIST_DIR.exists()
        and FINGERPRINT_FILE.read_text(encoding="utf-8").strip() == cache_fp
    ):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
            index = load_index_from_storage(storage_context)
            return index, [p.name for p in files], []
        except Exception:
            logger.warning("Could not load saved index; rebuilding.")

    documents, errors = load_all_documents(files)
    if not documents:
        return None, [], errors

    use_openai = config["provider"] == "openai"
    index = build_index_resilient(documents, use_openai=use_openai)
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
    FINGERPRINT_FILE.write_text(cache_fp, encoding="utf-8")

    return index, [d.metadata["filename"] for d in documents], errors


def create_chat_engine(index, config: dict[str, str], history: list[dict[str, str]] | None = None):
    from llama_index.core import Settings
    from llama_index.core.chat_engine import CondensePlusContextChatEngine
    from llama_index.core.llms import ChatMessage, MessageRole
    from llama_index.core.memory import ChatMemoryBuffer

    configure_llama_settings(config)
    memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
    for msg in history or []:
        role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
        memory.put(ChatMessage(role=role, content=msg["content"]))

    return CondensePlusContextChatEngine.from_defaults(
        retriever=index.as_retriever(similarity_top_k=5),
        llm=Settings.llm,
        memory=memory,
        system_prompt=SYSTEM_PROMPT,
        verbose=False,
    )


def format_citation_html(response_text: str) -> str:
    """Wrap citation lines in a styled callout if present."""
    lines = response_text.strip().splitlines()
    citation_lines: list[str] = []
    body_lines: list[str] = []
    in_citations = True

    for line in lines:
        stripped = line.strip()
        if in_citations and ("🏛️" in stripped or "Organization:" in stripped):
            citation_lines.append(stripped)
        elif in_citations and stripped == "" and not citation_lines:
            continue
        else:
            in_citations = False
            body_lines.append(line)

    if citation_lines:
        citations_html = "<br>".join(citation_lines)
        body_html = "<br>".join(body_lines).replace("\n", "<br>")
        return (
            f'<div class="citation-box"><strong>📋 Official Source Citations</strong><br><br>'
            f"{citations_html}</div>{body_html}"
        )
    return response_text.replace("\n", "<br>")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    defaults = {
        "messages": [],
        "chat_engine": None,
        "admin_unlocked": False,
        "corpus_fingerprint": "",
        "indexed_files": [],
        "ingest_errors": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.chat_engine = None


# ---------------------------------------------------------------------------
# UI components
# ---------------------------------------------------------------------------
def render_header() -> None:
    st.markdown(
        """
        <div class="gov-header">
            <h1>🏛️ Government Regulatory AI Assistant</h1>
            <p>Official circulars, guidelines &amp; regulations — with verified citations</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, ok: bool, detail: str = "") -> None:
    css_class = "status-ok" if ok else "status-error"
    icon = "✅" if ok else "⚠️"
    detail_html = f" — {detail}" if detail else ""
    st.markdown(
        f'<span class="status-badge {css_class}">{icon} {label}{detail_html}</span>',
        unsafe_allow_html=True,
    )


def config_snapshot(config: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(config.items()))


def render_sidebar(config: dict[str, str], files: list[Path]) -> None:
    with st.sidebar:
        st.markdown('<p class="sidebar-title">System Status</p>', unsafe_allow_html=True)

        if config["provider"] == "openai":
            render_status_badge("OpenAI API Key", bool(config["openai_api_key"]))
            st.caption(f"Model: {config['openai_model']}")
        else:
            ollama_ok = ollama_is_running(config["ollama_base_url"])
            render_status_badge("Ollama Running", ollama_ok, "Free local AI")
            st.caption(f"Model: {config['ollama_model']}")

        render_status_badge("Knowledge Base Ready", is_ai_ready(config) and len(files) > 0, "Indexed")
        st.markdown(
            f'<span class="status-badge status-ok">📄 Active Documents: {len(files)}</span>',
            unsafe_allow_html=True,
        )

        if st.session_state.ingest_errors:
            st.markdown(
                f'<span class="status-badge status-warn">⚠️ {len(st.session_state.ingest_errors)} file(s) skipped</span>',
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown('<p class="sidebar-title">Session</p>', unsafe_allow_html=True)
        st.caption(f"Messages: {len(st.session_state.messages)}")
        if st.button("🔄 Clear Conversation", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.divider()
        st.markdown('<p class="sidebar-title">Administrator</p>', unsafe_allow_html=True)

        if st.session_state.admin_unlocked:
            st.success("Admin access granted")
            with st.expander("📁 Document Management Guide", expanded=True):
                st.markdown(
                    f"""
                    **Adding new documents**

                    1. Place PDF, DOCX, or TXT files in:
                       `{DATA_SOURCE_DIR.name}/`
                    2. Use descriptive filenames, e.g.  
                       `Finance_Ministry_Circular_2023.pdf`
                    3. Click **Rebuild Knowledge Base** below.
                    4. Documents are indexed automatically on next load.

                    **Supported formats:** PDF, DOCX, TXT, MD  
                    **Indexed files:** {len(st.session_state.indexed_files)}

                    **Deployment note:** On Streamlit Cloud, upload files via
                    GitHub (commit to `data_source/`) or rebuild after redeploy.
                    """
                )
                if st.session_state.ingest_errors:
                    st.warning("Files with errors:")
                    for err in st.session_state.ingest_errors:
                        st.caption(f"• {err}")

            if st.button("🔨 Rebuild Knowledge Base", use_container_width=True):
                get_vector_index.clear()
                reset_conversation()
                st.session_state.corpus_fingerprint = ""
                if INDEX_CACHE_DIR.exists():
                    shutil.rmtree(INDEX_CACHE_DIR, ignore_errors=True)
                st.rerun()

            if st.button("🔒 Lock Admin Panel", use_container_width=True):
                st.session_state.admin_unlocked = False
                st.rerun()
        else:
            pwd = st.text_input("Admin password", type="password", key="admin_pwd_input")
            if st.button("Unlock Admin Panel", use_container_width=True):
                if pwd == config["admin_password"]:
                    st.session_state.admin_unlocked = True
                    st.rerun()
                elif pwd:
                    st.error("Incorrect password.")

        st.divider()
        st.caption(f"© {datetime.now().year} · tharshan.lk · {config['provider'].upper()}")


def initialize_rag(config: dict[str, str], files: list[Path]) -> bool:
    if not is_ai_ready(config):
        return False
    if not files:
        return False

    fingerprint = compute_corpus_fingerprint(files)
    if (
        st.session_state.corpus_fingerprint == fingerprint
        and st.session_state.chat_engine is not None
    ):
        return True

    try:
        mkey = model_cache_key(config)
        cache_fp = f"{fingerprint}:{mkey}"
        cached = (
            FINGERPRINT_FILE.exists()
            and PERSIST_DIR.exists()
            and FINGERPRINT_FILE.read_text(encoding="utf-8").strip() == cache_fp
        )

        provider_label = "Ollama (local)" if config["provider"] != "openai" else "OpenAI"

        with st.status(
            "Loading knowledge base from cache…" if cached else "Indexing government documents…",
            expanded=not cached,
        ) as status:
            if not cached:
                st.write("📖 **Step 1/2** — Reading your PDF files…")
                for path in files:
                    st.caption(f"• {path.name}")
                st.write(
                    f"🔄 **Step 2/2** — Indexing with **{provider_label}**.\n\n"
                    "**First time only:** large manuals can take **10–30 minutes** on Ollama "
                    "(free, runs on your PC). Keep this tab open."
                )
            else:
                st.write("✅ Using saved index — no re-indexing needed.")

            index, indexed_files, errors = get_vector_index(
                mkey,
                fingerprint,
                config_snapshot(config),
            )

            if cached:
                status.update(label="Knowledge base loaded from cache", state="complete")
            else:
                status.update(label="Indexing complete — ready to chat", state="complete")
        st.session_state.ingest_errors = errors
        st.session_state.indexed_files = indexed_files
        st.session_state.corpus_fingerprint = fingerprint

        if index is None:
            st.session_state.chat_engine = None
            return False

        st.session_state.chat_engine = create_chat_engine(
            index,
            config,
            history=st.session_state.messages,
        )
        return True
    except Exception as exc:
        logger.exception("RAG initialization failed")
        st.session_state.chat_engine = None
        if _is_rate_limit_error(exc):
            st.error("OpenAI rate limit or quota reached while indexing documents.")
            st.markdown(
                """
                **Switch to free local AI instead:**

                1. Install [Ollama](https://ollama.com/download)
                2. In terminal run:
                   ```
                   ollama pull llama3.2
                   ollama pull nomic-embed-text
                   ```
                3. In `.streamlit/secrets.toml` set: `AI_PROVIDER = "ollama"`
                4. Restart the app

                Or add billing at [platform.openai.com/settings/billing](https://platform.openai.com/settings/billing).
                """
            )
        else:
            st.error(
                f"Unable to initialize the knowledge base. Please contact your administrator. ({type(exc).__name__})"
            )
        return False


def render_chat(config: dict[str, str]) -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(format_citation_html(message["content"]), unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask about circulars, guidelines, or regulations…"):
        if not is_ai_ready(config):
            st.warning("AI engine is not ready. Check sidebar status and secrets.toml.")
            return

        if st.session_state.chat_engine is None:
            st.warning("Knowledge base is not ready. Add documents to `data_source/` and refresh.")
            return

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching official documents…"):
                try:
                    response = st.session_state.chat_engine.chat(prompt)
                    answer = str(response)
                except Exception as exc:
                    logger.exception("Chat request failed")
                    answer = (
                        "I apologize — a temporary error occurred while processing your request. "
                        "Please try again in a moment. If the issue persists, contact your system administrator."
                    )
                    st.caption(f"Error detail (admin): {type(exc).__name__}")

            st.markdown(format_citation_html(answer), unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": answer})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Government Regulatory AI Assistant",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(GOVERNMENT_CSS, unsafe_allow_html=True)

    init_session_state()
    config = get_config()
    files = scan_data_source()

    render_sidebar(config, files)
    render_header()

    if not is_ai_ready(config):
        if config["provider"] == "openai":
            st.info(
                "**Configuration required.** Add your `OPENAI_API_KEY` to `.streamlit/secrets.toml` "
                "or switch to free local AI: `AI_PROVIDER = \"ollama\"`"
            )
        else:
            st.info(
                "**Ollama is not running.** Install it from [ollama.com/download](https://ollama.com/download), "
                "then run in a terminal:\n\n"
                "```\nollama pull llama3.2\nollama pull nomic-embed-text\n```\n\n"
                "Keep Ollama open in the background, then refresh this page."
            )
        return

    if not files:
        st.warning(
            f"No documents found in `{DATA_SOURCE_DIR.name}/`. "
            "Administrators can add PDF or Word files and rebuild the knowledge base from the sidebar."
        )
        st.markdown(
            """
            **Example queries once documents are loaded:**
            - *What are the leave entitlements under the latest public service circular?*
            - *Summarize procurement guidelines for values above the threshold limit.*
            - *Which section covers disciplinary procedures?*
            """
        )
        return

    if initialize_rag(config, files):
        render_chat(config)


if __name__ == "__main__":
    main()
