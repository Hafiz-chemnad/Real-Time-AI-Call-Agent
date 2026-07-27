from typing import List, Optional


class VectorlessRetriever:
    """
    Simple keyword-based knowledge retriever.
    """

    def __init__(self, knowledge: List[str]):
        self.knowledge = knowledge

    def retrieve(self, query: str) -> Optional[str]:

        query = query.lower()

        results = []

        for item in self.knowledge:

            text = item.lower()

            score = 0

            for word in query.split():

                if word in text:
                    score += 1

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