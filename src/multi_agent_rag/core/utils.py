def get_text_content(content):
    """
    Safely extract text from potentially multimodal message content.

    Args:
        content: String or list of content parts.

    Returns:
        str: The extracted text content.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    text_parts.append(c.get("text", ""))
            elif (
                hasattr(c, "type") and c.type == "text"
            ):  # Handle LangChain message objects
                text_parts.append(getattr(c, "text", ""))
            elif hasattr(c, "get") and c.get("type") == "text":
                text_parts.append(c.get("text", ""))
        return " ".join(text_parts)
    return str(content)
