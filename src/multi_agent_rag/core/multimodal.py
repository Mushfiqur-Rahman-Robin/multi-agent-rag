import base64

import aiofiles
from langchain_core.messages import HumanMessage

from src.multi_agent_rag.core.file_extractor import extract_file_content


async def encode_image(image_path):
    async with aiofiles.open(image_path, "rb") as image_file:
        content = await image_file.read()
        return base64.b64encode(content).decode("utf-8")


async def create_multimodal_message(text: str, file_paths: list = None):
    # Initialize content list with the user's main query text
    content = [{"type": "text", "text": text}]

    if file_paths:
        for path in file_paths:
            path_lower = path.lower()

            # Handle Images
            if path_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_data = await encode_image(path)
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    }
                )

            # Handle Audio
            elif path_lower.endswith((".mp3", ".wav", ".m4a")):
                async with aiofiles.open(path, "rb") as f:
                    content_bytes = await f.read()
                    audio_base64 = base64.b64encode(content_bytes).decode("utf-8")
                content.append(
                    {
                        "type": "media",
                        "mime_type": f"audio/{path_lower.split('.')[-1]}",
                        "data": audio_base64,
                    }
                )

            # Handle Documents (PDF, DOCX, TXT, Code)
            else:
                # Attempt to extract text content
                extracted_text = await extract_file_content(path)
                if extracted_text:
                    filename = path.split("/")[-1]
                    content.append(
                        {
                            "type": "text",
                            "text": f"\n\n--- Attached File: {filename} ---\n{extracted_text}\n--- End of File ---\n",
                        }
                    )

    return HumanMessage(content=content)
