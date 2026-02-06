import base64

import aiofiles
from langchain_core.messages import HumanMessage


async def encode_image(image_path):
    async with aiofiles.open(image_path, "rb") as image_file:
        content = await image_file.read()
        return base64.b64encode(content).decode("utf-8")


async def create_multimodal_message(text: str, file_paths: list = None):
    content = [{"type": "text", "text": text}]

    if file_paths:
        for path in file_paths:
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_data = await encode_image(path)
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    }
                )
            elif path.lower().endswith((".mp3", ".wav", ".m4a")):
                async with aiofiles.open(path, "rb") as f:
                    content_bytes = await f.read()
                    audio_base64 = base64.b64encode(content_bytes).decode("utf-8")
                content.append(
                    {
                        "type": "media",
                        "mime_type": f"audio/{path.split('.')[-1]}",
                        "data": audio_base64,
                    }
                )

    return HumanMessage(content=content)
