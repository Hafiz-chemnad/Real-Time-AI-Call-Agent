import json

def retrieve_faq_context(query: str) -> str:
    try:
        with open("data/faq_data.json", "r") as file:
            faq_data = json.load(file)
    except FileNotFoundError:
        return ""

    context = ""
    for item in faq_data:
        keywords = item.get("keywords", [])
        if any(keyword.lower() in query.lower() for keyword in keywords):
            context += f"{item.get('answer')}\n"

    return context.strip()