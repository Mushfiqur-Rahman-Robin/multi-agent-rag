"""
File extraction module for the Aura Multi-Agent RAG system.

Provides utilities to extract text content from various file formats (PDF, DOCX, TXT)
to be included in the LLM context.
"""

import logging

import aiofiles
import docx2txt
from pypdf import PdfReader

logger = logging.getLogger(__name__)


async def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF content from {file_path}: {e}")
        return f"[Error extracting PDF: {e}]"


async def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        # docx2txt is synchronous, but fast enough for typical docs.
        # We could run this in a thread if blocking becomes an issue.
        text = docx2txt.process(file_path)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting DOCX content from {file_path}: {e}")
        return f"[Error extracting DOCX: {e}]"


async def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a plain text file."""
    try:
        async with aiofiles.open(file_path, encoding="utf-8", errors="replace") as f:
            return await f.read()
    except Exception as e:
        logger.error(f"Error extracting TXT content from {file_path}: {e}")
        return f"[Error extracting TXT: {e}]"


async def extract_file_content(file_path: str) -> str:
    """
    Dispatch file extraction based on extension.
    Returns the extracted text string.
    """
    path_lower = file_path.lower()

    if path_lower.endswith(".pdf"):
        return await extract_text_from_pdf(file_path)
    elif path_lower.endswith(".docx"):
        return await extract_text_from_docx(file_path)
    elif path_lower.endswith(
        (
            ".txt",
            ".md",
            ".csv",
            ".json",
            ".py",
            ".js",
            ".html",
            ".css",
            ".yml",
            ".yaml",
            ".xml",
        )
    ):
        return await extract_text_from_txt(file_path)

    return ""
