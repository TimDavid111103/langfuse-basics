from dataclasses import dataclass
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


@dataclass
class PageContent:
    """A single Docling document item (paragraph, list entry, or table) with its provenance."""

    page_number: int | None
    section_title: str | None
    text: str


def _make_converter() -> DocumentConverter:
    """Build a Docling DocumentConverter configured for CPU-based PDF processing."""
    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CPU),
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )


def extract_content(file_path: Path) -> list[PageContent]:
    """Parse a PDF and return one PageContent per document item.

    Docling segments PDFs into typed items (TextItem, TableItem, ListItem,
    SectionHeaderItem, etc.). Section headers update a running tracker so each
    subsequent item carries the correct section_title. Tables are exported as
    Markdown; all other text items use the plain .text attribute.
    """
    converter = _make_converter()
    result = converter.convert(str(file_path))
    doc = result.document

    pages: list[PageContent] = []
    current_section: str | None = None

    for item, _level in doc.iterate_items():
        item_type = type(item).__name__

        if item_type == "SectionHeaderItem":
            current_section = item.text.strip()
            continue

        if item_type in ("TextItem", "TableItem", "ListItem"):
            if item_type == "TableItem":
                text = item.export_to_markdown()
            else:
                text = item.text
            text = text.strip()
            if not text:
                continue

            page_no: int | None = None
            if hasattr(item, "prov") and item.prov:
                page_no = item.prov[0].page_no

            pages.append(
                PageContent(
                    page_number=page_no,
                    section_title=current_section,
                    text=text,
                )
            )

    return pages


def count_pages(file_path: Path) -> int | None:
    """Return the total page count of a PDF, or None if Docling cannot determine it."""
    converter = _make_converter()
    result = converter.convert(str(file_path))
    pages = result.document.pages
    return len(pages) if pages else None
