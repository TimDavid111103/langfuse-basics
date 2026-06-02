"""
Ingest PDF files into the database with embeddings.

Usage:
    # Ingest all PDFs in data/materials/
    uv run python scripts/ingest.py

    # Ingest specific files
    uv run python scripts/ingest.py data/materials/chapter8.pdf path/to/other.pdf

Run from the backend/ directory.
"""
import asyncio
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

from app.database import AsyncSessionLocal, create_db_and_tables
from app.models.source_material import IngestionStatus, MaterialType, SourceMaterial
from app.services.ingestion.chunker import chunk_pages
from app.services.ingestion.embedder import embed_and_store
from app.services.ingestion.pdf_extractor import count_pages, extract_content

MATERIALS_DIR = Path(__file__).parent.parent / "data" / "materials"


async def ingest_file(file_path: Path) -> None:
    content = file_path.read_bytes()
    file_hash = hashlib.sha256(content).hexdigest()

    async with AsyncSessionLocal() as session:
        existing = await session.exec(
            select(SourceMaterial).where(SourceMaterial.file_hash == file_hash)
        )
        if existing.first():
            print(f"  skip  {file_path.name}  (already ingested)")
            return

        material = SourceMaterial(
            name=file_path.stem,
            filename=str(file_path.resolve()),
            original_filename=file_path.name,
            file_hash=file_hash,
            material_type=MaterialType.PDF,
            ingestion_status=IngestionStatus.PROCESSING,
        )
        session.add(material)
        await session.commit()
        await session.refresh(material)

        try:
            pages = extract_content(file_path)
            page_count = count_pages(file_path)
            chunks = chunk_pages(pages)

            material.page_count = page_count
            session.add(material)
            await session.flush()

            await embed_and_store(chunks, material.id, session)

            material.ingestion_status = IngestionStatus.COMPLETE
            session.add(material)
            await session.commit()
            print(f"  ok    {file_path.name}  ({page_count} pages, {len(chunks)} chunks, id={material.id})")

        except Exception as exc:
            await session.rollback()
            async with AsyncSessionLocal() as err_session:
                r = await err_session.exec(
                    select(SourceMaterial).where(SourceMaterial.id == material.id)
                )
                m = r.one()
                m.ingestion_status = IngestionStatus.FAILED
                m.ingestion_error = str(exc)
                err_session.add(m)
                await err_session.commit()
            print(f"  fail  {file_path.name}  {exc}")
            raise


async def main(paths: list[Path]) -> None:
    await create_db_and_tables()
    for path in paths:
        print(f"ingesting {path.name} ...")
        await ingest_file(path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    else:
        targets = sorted(MATERIALS_DIR.glob("*.pdf"))
        if not targets:
            print(f"No PDFs found in {MATERIALS_DIR}")
            sys.exit(0)

    asyncio.run(main(targets))
