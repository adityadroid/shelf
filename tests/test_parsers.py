from __future__ import annotations

from pathlib import Path

from docx import Document
from reportlab.pdfgen import canvas

from shelf.indexing.models import ParserStatus
from shelf.parsers.doc_parser import DocParser
from shelf.parsers.registry import ParserRegistry


def create_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, text)
    pdf.save()


def create_docx(path: Path, text: str) -> None:
    document = Document()
    document.add_paragraph(text)
    document.save(path)


def test_pdf_and_docx_parsers_extract_text(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    docx_path = tmp_path / "sample.docx"
    create_pdf(pdf_path, "shelf pdf text")
    create_docx(docx_path, "shelf docx text")

    registry = ParserRegistry()
    pdf_result = registry.parse(pdf_path)
    docx_result = registry.parse(docx_path)

    assert pdf_result.parser_status == ParserStatus.SUCCESS
    assert "shelf pdf text" in pdf_result.raw_text
    assert docx_result.parser_status == ParserStatus.SUCCESS
    assert "shelf docx text" in docx_result.raw_text


def test_doc_parser_reports_missing_antiword(tmp_path):
    doc_path = tmp_path / "legacy.doc"
    doc_path.write_bytes(b"not-really-doc")

    result = DocParser().parse(doc_path)

    assert result.parser_status in {ParserStatus.FAILURE, ParserStatus.NO_TEXT}
    assert result.diagnostics


def test_text_and_markdown_parsers_extract_text(tmp_path):
    txt_path = tmp_path / "notes.txt"
    md_path = tmp_path / "notes.md"
    txt_path.write_text("plain shelf text", encoding="utf-8")
    md_path.write_text("# Shelf\n\nmarkdown body", encoding="utf-8")

    registry = ParserRegistry()
    txt_result = registry.parse(txt_path)
    md_result = registry.parse(md_path)

    assert txt_result.parser_status == ParserStatus.SUCCESS
    assert txt_result.raw_text == "plain shelf text"
    assert md_result.parser_status == ParserStatus.SUCCESS
    assert "markdown body" in md_result.raw_text
