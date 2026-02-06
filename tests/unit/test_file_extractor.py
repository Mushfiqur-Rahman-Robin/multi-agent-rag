
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import aiofiles
from src.multi_agent_rag.core.file_extractor import extract_file_content, extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt

@pytest.mark.asyncio
async def test_extract_pdf(tmp_path):
    # We can't easily create a valid PDF in a test without dependencies, so we mock pypdf
    with patch("src.multi_agent_rag.core.file_extractor.PdfReader") as MockPdfReader:
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF Content"
        mock_reader.pages = [mock_page]
        MockPdfReader.return_value = mock_reader

        content = await extract_text_from_pdf("dummy.pdf")
        assert content == "PDF Content"

@pytest.mark.asyncio
async def test_extract_docx():
    with patch("src.multi_agent_rag.core.file_extractor.docx2txt.process") as mock_process:
        mock_process.return_value = "DOCX Content"
        content = await extract_text_from_docx("dummy.docx")
        assert content == "DOCX Content"

@pytest.mark.asyncio
async def test_extract_txt(tmp_path):
    d = tmp_path / "test.txt"
    d.write_text("TXT Content", encoding="utf-8")

    content = await extract_text_from_txt(str(d))
    assert content == "TXT Content"

@pytest.mark.asyncio
async def test_extract_file_content_dispatch():
    with patch("src.multi_agent_rag.core.file_extractor.extract_text_from_pdf", new_callable=AsyncMock) as mock_pdf:
        mock_pdf.return_value = "PDF"
        assert await extract_file_content("test.pdf") == "PDF"

    with patch("src.multi_agent_rag.core.file_extractor.extract_text_from_docx", new_callable=AsyncMock) as mock_docx:
        mock_docx.return_value = "DOCX"
        assert await extract_file_content("test.docx") == "DOCX"

    with patch("src.multi_agent_rag.core.file_extractor.extract_text_from_txt", new_callable=AsyncMock) as mock_txt:
        mock_txt.return_value = "TXT"
        assert await extract_file_content("test.py") == "TXT"
