"""
Document processing service: PDF parsing, OCR, text extraction, chunking
"""

import os
import mimetypes
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import PyPDF2
from docx import Document as DocxDocument
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process various document types and extract text"""
    
    def __init__(self):
        if settings.OCR_PROVIDER == "tesseract" and settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def process_document(self, file_path: str, file_type: str) -> Dict:
        """
        Process a document and extract text with metadata
        
        Returns:
            dict with keys: text, page_count, requires_ocr, pages (list of page texts)
        """
        try:
            if file_type.lower() == "pdf":
                return self._process_pdf(file_path)
            elif file_type.lower() in ["docx", "doc"]:
                return self._process_docx(file_path)
            elif file_type.lower() == "txt":
                return self._process_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def _process_pdf(self, file_path: str) -> Dict:
        """Process PDF file"""
        text_pages = []
        requires_ocr = False
        
        try:
            # Try text extraction first
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_pages.append({
                                "page_number": page_num,
                                "text": page_text,
                                "method": "extraction"
                            })
                        else:
                            # No text found, mark for OCR
                            requires_ocr = True
                            text_pages.append({
                                "page_number": page_num,
                                "text": "",
                                "method": "ocr_needed"
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num}: {e}")
                        requires_ocr = True
                        text_pages.append({
                            "page_number": page_num,
                            "text": "",
                            "method": "ocr_needed"
                        })
            
            # If OCR is needed, process pages
            if requires_ocr:
                logger.info(f"Performing OCR on PDF: {file_path}")
                ocr_pages = self._ocr_pdf(file_path)
                for i, ocr_text in enumerate(ocr_pages):
                    if text_pages[i]["text"] == "":
                        text_pages[i]["text"] = ocr_text
                        text_pages[i]["method"] = "ocr"
            
            full_text = "\n\n".join([page["text"] for page in text_pages])
            
            return {
                "text": full_text,
                "page_count": page_count,
                "requires_ocr": requires_ocr,
                "pages": text_pages
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise
    
    def _ocr_pdf(self, file_path: str) -> List[str]:
        """Perform OCR on PDF pages"""
        try:
            # Convert PDF to images
            images = convert_from_path(file_path, dpi=300)
            ocr_texts = []
            
            for image in images:
                # Perform OCR
                ocr_text = pytesseract.image_to_string(image, lang='eng')
                ocr_texts.append(ocr_text)
            
            return ocr_texts
        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return [""] * len(images) if 'images' in locals() else []
    
    def _process_docx(self, file_path: str) -> Dict:
        """Process DOCX file"""
        try:
            doc = DocxDocument(file_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            full_text = "\n\n".join(paragraphs)
            
            # Estimate page count (rough: ~500 words per page)
            word_count = len(full_text.split())
            estimated_pages = max(1, word_count // 500)
            
            return {
                "text": full_text,
                "page_count": estimated_pages,
                "requires_ocr": False,
                "pages": [{"page_number": 1, "text": full_text, "method": "extraction"}]
            }
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            raise
    
    def _process_txt(self, file_path: str) -> Dict:
        """Process TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            
            # Estimate page count
            word_count = len(text.split())
            estimated_pages = max(1, word_count // 500)
            
            return {
                "text": text,
                "page_count": estimated_pages,
                "requires_ocr": False,
                "pages": [{"page_number": 1, "text": text, "method": "extraction"}]
            }
        except Exception as e:
            logger.error(f"Error processing TXT {file_path}: {e}")
            raise
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = None, 
        chunk_overlap: int = None,
        preserve_paragraphs: bool = True
    ) -> List[Dict]:
        """
        Chunk text into smaller pieces for vector search
        
        Args:
            text: Full text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            preserve_paragraphs: Try to keep paragraphs intact
        
        Returns:
            List of chunk dicts with: content, start_char, end_char, chunk_index
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        chunks = []
        
        if preserve_paragraphs:
            # Split by paragraphs first
            paragraphs = text.split('\n\n')
            current_chunk = ""
            current_start = 0
            chunk_index = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # If adding this paragraph would exceed chunk size, save current chunk
                if current_chunk and len(current_chunk) + len(para) + 2 > chunk_size:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "start_char": current_start,
                        "end_char": current_start + len(current_chunk),
                        "chunk_index": chunk_index
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    if chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                        current_start = current_start + len(current_chunk) - len(overlap_text) - len(para) - 2
                    else:
                        current_chunk = para
                        current_start = len(text) - len(text[current_start:]) if chunks else 0
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                        if not chunks:
                            current_start = 0
                        else:
                            # Calculate start position
                            current_start = sum(len(c["content"]) for c in chunks)
            
            # Add final chunk
            if current_chunk:
                chunks.append({
                    "content": current_chunk.strip(),
                    "start_char": current_start,
                    "end_char": current_start + len(current_chunk),
                    "chunk_index": chunk_index
                })
        else:
            # Simple character-based chunking
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk_text = text[i:i + chunk_size]
                chunks.append({
                    "content": chunk_text.strip(),
                    "start_char": i,
                    "end_char": min(i + len(chunk_text), len(text)),
                    "chunk_index": len(chunks)
                })
        
        return chunks



