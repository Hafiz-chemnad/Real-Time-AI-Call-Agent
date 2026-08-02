from typing import List, Optional

import re
class VectorlessRetriever:
    """
    Simple keyword-based knowledge retriever.
    """

    def __init__(self, knowledge: List[str]):
        self.knowledge = knowledge

    

    def _tokenize(self,text: str) -> List[str]:
        return re.findall(r"[a-z0-9']+", text.lower())

    def retrieve(self, query: str) -> Optional[str]:
        query_words = set(self._tokenize(query))
        results = []
        for item in self.knowledge:
          text_words = set(self._tokenize(item))
          score = len(query_words & text_words)
          results.append((score, item))
        if not results:
          return None
        results.sort(reverse=True)
        if results[0][0] == 0:
          return None
        return results[0][1]


def retrieve(query: str, knowledge: List[str]) -> Optional[str]:
    retriever = VectorlessRetriever(knowledge)
    return retriever.retrieve(query)