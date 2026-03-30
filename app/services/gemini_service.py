import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from app.services.rag_service import retrieve

load_dotenv()

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Bind native Google Search grounding tool
_llm_with_search = _llm.bind(tools=[{"google_search": {}}])


def search_with_gemini(query: str) -> dict:
    """Send a query to Gemini via LangChain with Google Search grounding."""
    try:
        response = _llm_with_search.invoke([HumanMessage(content=query)])
        answer = response.content or ""

        sources = []
        grounding = response.response_metadata.get("grounding_metadata", {})
        for chunk in grounding.get("grounding_chunks", []):
            web = chunk.get("web", {})
            if web.get("uri"):
                sources.append({
                    "title": web.get("title") or web["uri"],
                    "uri": web["uri"],
                })

        return {"answer": answer, "sources": sources}

    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            raise RuntimeError(
                "Gemini API quota exceeded. The free tier daily limit has been reached. "
                "Please wait until tomorrow or enable billing at https://ai.google.dev."
            ) from e
        raise RuntimeError(f"Gemini API error: {e}") from e


def search_with_rag(query: str) -> dict:
    """Retrieve relevant chunks from local docs, then answer with Gemini."""
    chunks = retrieve(query, k=4)
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""Answer the question using ONLY the context below.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {query}
"""
    try:
        response = _llm.invoke([HumanMessage(content=prompt)])
        return {
            "answer": response.content or "",
            "chunks": chunks,
        }
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            raise RuntimeError(
                "Gemini API quota exceeded. The free tier daily limit has been reached. "
                "Please wait until tomorrow or enable billing at https://ai.google.dev."
            ) from e
        raise RuntimeError(f"RAG error: {e}") from e
