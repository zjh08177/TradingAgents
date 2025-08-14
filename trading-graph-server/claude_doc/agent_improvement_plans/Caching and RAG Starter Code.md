# LangGraph Cloud: Caching & RAG (How‑To + Starter Code)

**Short answer:** Yes—you can implement both caching and RAG entirely with LangGraph/LangChain and deploy it on **LangGraph Cloud**, using built‑in primitives plus your choice of vector store/DB. No extra orchestration layer is required.

---

## What you’ll build

- **Caching, three layers**
  1. **Node‑level cache (LangGraph):** cache a node’s output by its input; set per‑node TTL; set graph‑wide cache backend.
  2. **LLM response cache (LangChain):** cache identical prompts across runs (SQLite/Redis/SQLAlchemy/etc.).
  3. **Embedding cache (LangChain):** avoid re‑embedding the same text via `CacheBackedEmbeddings`.
- **RAG inside the graph**: vector store → retriever → model tool or retrieval node.
- **Persistence on Cloud**: threads/checkpoints are handled; pass a `thread_id` to continue context. Use the built‑in **Store** for long‑term, searchable memory (Postgres + pgvector on Cloud).

---

## Design blueprint

**Graph state (example)**

- `messages`: chat history (append reducer)
- `context`: retrieved text
- `answer`: final model reply

**Recommended wiring**

1. **Plan/decide**: let the model decide whether to retrieve or answer directly (`bind_tools` with a retriever tool).
2. **Retrieve**: call retriever → dedupe/rerank; **cache this node** (e.g., TTL 1h).
3. **Answer**: combine question + context to produce response.
4. **Persistence**: invoke with `config={"configurable": {"thread_id": "..."}}` so Cloud restores memory/history.
5. **Store / memory** (optional): in any node, accept `store: BaseStore` to `put/get/search` JSON memories; enable semantic search when configured (pgvector).

---

## Minimal Python starter

```python
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

# --- LangChain: caches & models ---
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools.retriever import create_retriever_tool

# --- Vector store / retriever ---
from langchain_core.vectorstores.in_memory import InMemoryVectorStore  # swap for pgvector/FAISS in prod

# --- LangGraph: graph, node cache, message state ---
from langgraph.graph import StateGraph, START, END
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy

# 0) Global LLM cache (persists if the file persists)
set_llm_cache(SQLiteCache(database_path=".lc_llm_cache.db"))  # or Redis/SQLAlchemy cache

# 1) Embedding cache (avoid recomputing embeddings)
embedder = OpenAIEmbeddings()
bytes_store = LocalFileStore("./embed_cache")
cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    embedder, bytes_store, namespace=embedder.model
)

# 2) Build a tiny vector store + retriever tool
vectorstore = InMemoryVectorStore(embedding=cached_embedder)
vectorstore.add_texts([
    "LangGraph supports node-level caching.",
    "RAG uses a retriever over your indexed docs.",
    "Checkpointers persist per-thread state.",
])
retriever = vectorstore.as_retriever()
retriever_tool = create_retriever_tool(
    retriever,
    name="retrieve_knowledge",
    description="Search internal knowledge relevant to the user query.",
)

# 3) Define graph state
class State(TypedDict):
    messages: Annotated[list, add]
    context: str
    answer: str

# 4) Nodes
llm = init_chat_model("openai:gpt-4o-mini", temperature=0)

# Let the model optionally request retrieval
def plan_or_call_tool(state: State):
    resp = llm.bind_tools([retriever_tool]).invoke(state.get("messages", []))
    return {"messages": [resp]}

# Retrieval node (cache this)
def retrieve(state: State):
    # Simple heuristic: use the latest human message as the query
    msgs = state.get("messages", [])
    try:
        last_user = next(m for m in reversed(msgs) if getattr(m, "type", getattr(m, "role", "")) in ("human", "user"))
        query = getattr(last_user, "content", "")
    except StopIteration:
        query = ""
    docs = retriever.invoke({"query": query})
    ctx = "\n\n".join(getattr(d, "page_content", str(d)) for d in docs)
    return {"context": ctx}

# Answer using retrieved context when available
def answer(state: State):
    question = ""
    for m in state.get("messages", []):
        if getattr(m, "type", getattr(m, "role", "")) in ("human", "user"):
            question = getattr(m, "content", "")
            break
    prompt = (
        "Answer concisely using this context if helpful:\n\n"
        f"{state.get('context','')}\n\nQ: {question}"
    )
    ai = llm.invoke([HumanMessage(content=prompt)])
    return {"messages": [ai], "answer": ai.content}

# 5) Build graph with node-level caching (cache retrieval for 1 hour)
builder = StateGraph(State)
builder.add_node("plan", plan_or_call_tool)
builder.add_node("retrieve", retrieve, cache_policy=CachePolicy(ttl=3600))
builder.add_node("answer", answer)
builder.add_edge(START, "plan")
builder.add_edge("plan", "retrieve")
builder.add_edge("retrieve", "answer")
builder.add_edge("answer", END)

# Graph-wide cache backend (in-memory; swap for Redis in prod)
graph = builder.compile(cache=InMemoryCache())

# --- Cloud usage tip ---
# On LangGraph Cloud, threads/checkpoints are managed for you—just pass a thread_id
config = {"configurable": {"thread_id": "user-123"}}

# Run
out = graph.invoke({
    "messages": [HumanMessage(content="How do I add RAG and caching in LangGraph?")]
}, config=config)
print(out["answer"])  # -> "..."
```

**What this gives you**

- **Node cache**: `retrieve` node memoized for identical inputs (TTL 1h).
- **LLM cache**: identical prompts are cached via SQLite (swap to Redis/SQLAlchemy for multi‑replicas).
- **Embedding cache**: re‑index or re‑deploy without paying to re‑embed unchanged text.
- **RAG**: retriever tool living inside the graph; extend to full **agentic RAG** (grade → rewrite → answer).
- **Cloud persistence**: supply `thread_id` to persist/continue across runs; use the **Store** for semantic long‑term memory.

---

## Deployment notes & tips

- **Cache keys**: for node caching, default key is a hash of node input; define a custom `key_func` if you need finer control.
- **LLM cache scope**: global to the process; choose a backend that’s shared by all replicas (e.g., Redis) in production.
- **Embedding cache namespace**: set the `namespace` to the embedding model name to prevent collisions across models.
- **Vector store**: start with `InMemoryVectorStore` for dev; move to **pgvector**/**FAISS**/**Pinecone** in prod.
- **Store (Cloud)**: use `store.put`/`store.get`/`store.search` inside nodes for cross‑thread memory; enable semantic index when you need meaning‑based queries.

---

## References

- **LangGraph → Node Caching (concepts)**: [https://langchain-ai.github.io/langgraph/concepts/low\_level/#node-caching](https://langchain-ai.github.io/langgraph/concepts/low_level/#node-caching)
- **LangGraph → Persistence, Threads, and **``: [https://langchain-ai.github.io/langgraph/concepts/persistence/](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- **LangGraph → Store (Postgres + optional pgvector)**: [https://langchain-ai.github.io/langgraph/reference/store/](https://langchain-ai.github.io/langgraph/reference/store/)
- **LangGraph → Agentic RAG tutorial**: [https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph\_agentic\_rag/](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/)
- **LangChain → **``** (core API)**: [https://python.langchain.com/api\_reference/core/globals/langchain\_core.globals.set\_llm\_cache.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_llm_cache.html)
- **LangChain → Caching embeddings (**``**)**: [https://python.langchain.com/docs/how\_to/caching\_embeddings/](https://python.langchain.com/docs/how_to/caching_embeddings/)
- **LangChain → **``** (core API)**: [https://python.langchain.com/api\_reference/core/tools/langchain\_core.tools.retriever.create\_retriever\_tool.html](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.retriever.create_retriever_tool.html)
- **LangChain → **``** (core API)**: [https://python.langchain.com/api\_reference/core/vectorstores/langchain\_core.vectorstores.in\_memory.InMemoryVectorStore.html](https://python.langchain.com/api_reference/core/vectorstores/langchain_core.vectorstores.in_memory.InMemoryVectorStore.html)
- **LangGraph Cloud → Platform API reference**: [https://langchain-ai.github.io/langgraph/cloud/reference/api/api\_ref.html](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)
- **LangChain → Tool calling guide (**``**)**: [https://python.langchain.com/docs/how\_to/tool\_calling/](https://python.langchain.com/docs/how_to/tool_calling/)

