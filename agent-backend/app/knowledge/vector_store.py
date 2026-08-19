"""Vector-mode knowledge base using Google Gemini Embeddings."""
import os
import logging
import warnings
from typing import List

# ✅ Permanently silence the Python 3.10 future warnings from Google's core API
warnings.filterwarnings("ignore", category=FutureWarning)

# ✅ Using the brand new, officially supported Google GenAI SDK
from google import genai
from google.genai import types
from sqlalchemy import select, delete

from app.db.session import AsyncSessionLocal
from app.models.knowledge_base import KnowledgeChunk 

logger = logging.getLogger(__name__)

# The new SDK automatically picks up GEMINI_API_KEY from your .env file
client = genai.Client()

async def get_embedding(text: str) -> List[float]:
    """
    Generates an embedding using the new Gemini SDK.
    We truncate the 3072-dimension output down to exactly 1536 dimensions 
    to perfectly match your existing pgvector database schema!
    """
    try:
        response = await client.aio.models.embed_content(
            model="gemini-embedding-001", 
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.error(f"Gemini embedding failed: {e}")
        return []

async def get_vector_context(transcript: str, business_id: str, top_k: int = 3) -> str:
    """Searches the knowledge_chunks table using pgvector cosine distance."""
    try:
        query_embedding = await get_embedding(transcript)
        if not query_embedding:
            return ""
            
        async with AsyncSessionLocal() as session:
            # Query chunks belonging ONLY to this business, ordered by closest match
            stmt = (
                select(KnowledgeChunk.content)
                .where(KnowledgeChunk.business_id == business_id)
                .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            )
            result = await session.execute(stmt)
            chunks = result.scalars().all()
            
            if not chunks:
                return ""
                
            # Combine the top chunks into a single context block
            return "\n\n".join(chunks)
            
    except Exception as e:
        logger.error(f"Error in vector similarity search: {e}")
        return ""

async def ingest_knowledge_base(business_id: str, raw_text: str):
    """Splits text into chunks, embeds them via Gemini, and saves to Postgres."""
    if not raw_text or not raw_text.strip():
        return
        
    # Simple chunking by paragraph (can be upgraded later if needed)
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 10]
    
    async with AsyncSessionLocal() as session:
        # Clear any old chunks for this business before re-ingesting
        await session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.business_id == business_id)
        )
        
        for chunk in paragraphs:
            embedding = await get_embedding(chunk)
            if embedding:
                db_chunk = KnowledgeChunk(
                    business_id=business_id,
                    content=chunk,
                    embedding=embedding
                )
                session.add(db_chunk)
                
        await session.commit()
        logger.info(f"Ingested {len(paragraphs)} vector chunks for business {business_id}")