from typing import List, Optional

from .vectorless import VectorlessRetriever


class KnowledgeSelector:
    """
    Selects the most relevant knowledge for a given question.
    """

    def __init__(self, knowledge: List[str]):
        self.retriever = VectorlessRetriever(knowledge)

    def get_context(self, question: str) -> Optional[str]:
        return self.retriever.retrieve(question)


def get_context(question: str, knowledge: List[str]) -> Optional[str]:
    selector = KnowledgeSelector(knowledge)
    return selector.get_context(question)