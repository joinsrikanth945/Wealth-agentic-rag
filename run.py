# Adapted from Enterprise IT Support Agentic RAG Copilot by Bappy Ahmed (Apache-2.0).
# Modified by Sreekanth Dara, 2026.
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
