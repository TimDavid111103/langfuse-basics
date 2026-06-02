from dataclasses import dataclass
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


@dataclass
class PageContent:
    page_number: int | None
    section_title: str | None
    text: str


def _make_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CPU),
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )


def extract_content(file_path: Path) -> list[PageContent]:
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
            text = item.export_to_markdown() if hasattr(item, "export_to_markdown") else str(item)
            text = text.strip()
            if not text:
                continue

            page_no: int | None = None
            if hasattr(item, "prov") and item.prov:
                prov = item.prov[0]
                if hasattr(prov, "page_no"):
                    page_no = prov.page_no

            pages.append(
                PageContent(
                    page_number=page_no,
                    section_title=current_section,
                    text=text,
                )
            )

    return pages


def count_pages(file_path: Path) -> int | None:
    converter = _make_converter()
    result = converter.convert(str(file_path))
    pages = result.document.pages
    if pages:
        return len(pages)
    return None
