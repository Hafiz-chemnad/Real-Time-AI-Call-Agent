import re

def is_malayalam_text(text: str) -> bool:
    """
    Checks if the text contains characters in the Malayalam Unicode block (0D00–0D7F).
    """
    return bool(re.search(r'[\u0D00-\u0D7F]', text))