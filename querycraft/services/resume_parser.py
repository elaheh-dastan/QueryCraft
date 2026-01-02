"""
Service for parsing PDF resumes and extracting text content
"""

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


class ResumeParser:
    """Service for parsing PDF resumes"""

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path | str) -> str:
        """
        Extract text content from a PDF file

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content from the PDF

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If PDF parsing fails
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {pdf_path}")

        logger.info(f"Extracting text from PDF: {pdf_path}")

        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                logger.debug(f"PDF has {len(pdf.pages)} pages")
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                        logger.debug(f"Extracted {len(page_text)} characters from page {page_num}")

            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
            return full_text

        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}", exc_info=True)
            raise Exception(f"Failed to parse PDF: {e}") from e

    @staticmethod
    def extract_text_from_directory(directory: Path | str) -> dict[str, str]:
        """
        Extract text from all PDF files in a directory

        Args:
            directory: Path to directory containing PDF files

        Returns:
            Dictionary mapping PDF filenames to their extracted text content
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        logger.info(f"Scanning directory for PDFs: {directory}")

        pdf_files = list(directory.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF file(s)")

        results: dict[str, str] = {}

        for pdf_file in pdf_files:
            try:
                text = ResumeParser.extract_text_from_pdf(pdf_file)
                results[pdf_file.name] = text
                logger.info(f"✓ Successfully parsed: {pdf_file.name}")
            except Exception as e:
                logger.error(f"✗ Failed to parse {pdf_file.name}: {e}")
                results[pdf_file.name] = ""  # Store empty string for failed files

        return results

