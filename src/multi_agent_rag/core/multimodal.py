import base64
from PIL import Image
import io
from langchain_core.messages import HumanMessage

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def create_multimodal_message(text: str, file_paths: list = None):
    content = [{"type": "text", "text": text}]
    
    if file_paths:
        for path in file_paths:
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_data = encode_image(path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                })
            elif path.lower().endswith((".mp3", ".wav", ".m4a")):
                with open(path, "rb") as f:
                    audio_base64 = base64.b64encode(f.read()).decode("utf-8")
                content.append({
                    "type": "media",
                    "mime_type": f"audio/{path.split('.')[-1]}",
                    "data": audio_base64
                })
                
    return HumanMessage(content=content)
