import logging
from typing import List, Optional, Any
from app.knowledge.vectorless import VectorlessRetriever
from app.knowledge.vector_store import get_vector_context

logger = logging.getLogger(__name__)


class KnowledgeSelector:
    """
    Selects the most relevant knowledge for a given question
    supporting both Vectorless (keyword) and Vector (Gemini) modes.
    """

    def __init__(self, knowledge: List[Any], business_id: Optional[str] = None):
        self.knowledge = knowledge
        self.business_id = business_id
        
        # Determine mode if a DB config object was passed, default to vectorless
        self.mode = "vectorless"
        raw_strings: List[str] = []

        if knowledge:
            first_item = knowledge[0]
            # Check if knowledge item is a DB model/object with attributes
            if hasattr(first_item, "mode"):
                self.mode = getattr(first_item, "mode", "vectorless")
                self.business_id = getattr(first_item, "business_id", business_id)
                content = getattr(first_item, "content", "")
                raw_strings = [content] if content else []
            # Check if knowledge item is a dict (business_service.get_business_knowledge's shape)
            elif isinstance(first_item, dict):
                self.mode = first_item.get("mode", "vectorless")
                content = first_item.get("content", "")
                raw_strings = [content] if content else []
            elif isinstance(first_item, str):
                raw_strings = knowledge
            else:
                raw_strings = [str(item) for item in knowledge]

        # Initialize the vectorless retriever as default / fallback
        self.retriever = VectorlessRetriever(raw_strings)

    async def get_context(self, question: str) -> Optional[str]:
        """
        Retrieves context using either Vector similarity or Vectorless keyword search.
        """
        if not self.knowledge:
            return None

        # 1. Vector Mode
        if self.mode == "vector" and self.business_id:
            try:
                context = await get_vector_context(question, str(self.business_id))
                if context:
                    return context
            except Exception as e:
                logger.error(f"Vector search failed in KnowledgeSelector: {e}")

        # 2. Vectorless Fallback
        return self.retriever.retrieve(question)


async def get_context(
    question: str, 
    knowledge: List[Any], 
    business_id: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function that initializes KnowledgeSelector and returns context.
    """
    selector = KnowledgeSelector(knowledge, business_id=business_id)
    return await selector.get_context(question)