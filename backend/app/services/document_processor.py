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
            elif file_type.lower() in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
                return self._process_image(file_path)
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
    
    def _process_image(self, file_path: str) -> Dict:
        """Process image file using OCR"""
        try:
            # Open image
            img = Image.open(file_path)
            
            # Perform OCR on the image
            logger.info(f"Performing OCR on image: {file_path}")
            ocr_text = pytesseract.image_to_string(img, lang='eng')
            
            # Images are always single page
            return {
                "text": ocr_text,
                "page_count": 1,
                "requires_ocr": True,
                "pages": [{"page_number": 1, "text": ocr_text, "method": "ocr"}]
            }
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            raise
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = None, 
        chunk_overlap: int = None,
        preserve_paragraphs: bool = True,
        page_mapping: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Chunk text into smaller pieces for vector search
        
        Args:
            text: Full text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            preserve_paragraphs: Try to keep paragraphs intact
            page_mapping: List of dicts with page boundaries: [{"page": 1, "start": 0, "end": 500}, ...]
        
        Returns:
            List of chunk dicts with: content, start_char, end_char, chunk_index, page_number
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        chunks = []
        
        # Helper function to find page number for a character position
        def find_page_number(char_pos: int) -> Optional[int]:
            """Find the page number for a given character position"""
            if not page_mapping:
                return None
            for page_info in page_mapping:
                if page_info["start"] <= char_pos < page_info["end"]:
                    return page_info["page"]
            # If position is beyond last page, return last page number
            if page_mapping and char_pos >= page_mapping[-1]["end"]:
                return page_mapping[-1]["page"]
            return None
        
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
                    end_pos = current_start + len(current_chunk)
                    chunks.append({
                        "content": current_chunk.strip(),
                        "start_char": current_start,
                        "end_char": end_pos,
                        "chunk_index": chunk_index,
                        "page_number": find_page_number(current_start)
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
                end_pos = current_start + len(current_chunk)
                chunks.append({
                    "content": current_chunk.strip(),
                    "start_char": current_start,
                    "end_char": end_pos,
                    "chunk_index": chunk_index,
                    "page_number": find_page_number(current_start)
                })
        else:
            # Simple character-based chunking
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk_text = text[i:i + chunk_size]
                end_pos = min(i + len(chunk_text), len(text))
                chunks.append({
                    "content": chunk_text.strip(),
                    "start_char": i,
                    "end_char": end_pos,
                    "chunk_index": len(chunks),
                    "page_number": find_page_number(i)
                })
        
        return chunks
    
    def generate_thumbnail(self, file_path: str, file_type: str, output_path: str) -> bool:
        """
        Generate a thumbnail image for a document
        
        Args:
            file_path: Path to the source document
            file_type: Type of document (pdf, jpg, png, etc.)
            output_path: Path where thumbnail should be saved
        
        Returns:
            True if thumbnail was generated successfully, False otherwise
        """
        try:
            if file_type.lower() == "pdf":
                return self._generate_pdf_thumbnail(file_path, output_path)
            elif file_type.lower() in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
                return self._generate_image_thumbnail(file_path, output_path)
            else:
                # Don't generate thumbnails for unsupported types
                logger.debug(f"Thumbnail generation not supported for file type: {file_type}")
                return False
        except Exception as e:
            logger.error(f"Error generating thumbnail for {file_path}: {e}")
            return False
    
    def _generate_pdf_thumbnail(self, pdf_path: str, output_path: str) -> bool:
        """Generate thumbnail from first page of PDF"""
        try:
            # Convert first page of PDF to image
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
            if not images:
                return False
            
            # Get first page image
            first_page = images[0]
            
            # Create thumbnail
            thumbnail = self._resize_image(first_page, settings.THUMBNAIL_SIZE)
            
            # Save thumbnail as JPEG
            thumbnail.save(output_path, "JPEG", quality=85)
            logger.info(f"Generated PDF thumbnail: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating PDF thumbnail: {e}")
            return False
    
    def _generate_image_thumbnail(self, image_path: str, output_path: str) -> bool:
        """Generate thumbnail from image file"""
        try:
            # Open image
            img = Image.open(image_path)
            
            # Handle orientation (EXIF data)
            if hasattr(img, '_getexif'):
                try:
                    exif = img._getexif()
                    if exif:
                        orientation = exif.get(274)  # Orientation tag
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                except Exception:
                    pass  # Ignore EXIF errors
            
            # Convert RGBA to RGB if necessary (for JPEG compatibility)
            if img.mode in ("RGBA", "P"):
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            
            # Create thumbnail
            thumbnail = self._resize_image(img, settings.THUMBNAIL_SIZE)
            
            # Save thumbnail as JPEG
            thumbnail.save(output_path, "JPEG", quality=85)
            logger.info(f"Generated image thumbnail: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating image thumbnail: {e}")
            return False
    
    def _resize_image(self, img: Image.Image, max_size: int) -> Image.Image:
        """Resize image maintaining aspect ratio"""
        # Calculate new size maintaining aspect ratio
        width, height = img.size
        if width > height:
            if width > max_size:
                new_width = max_size
                new_height = int((height * max_size) / width)
            else:
                return img
        else:
            if height > max_size:
                new_height = max_size
                new_width = int((width * max_size) / height)
            else:
                return img
        
        # Resize with high-quality resampling
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)




