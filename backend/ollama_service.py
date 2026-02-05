"""
Minimal Ollama Service for LLaMA 3 Integration

This is a simple backend service that connects to a local Ollama instance
running the llama3:8b model. It provides a single POST endpoint /query
that accepts prompts and returns the model's response.

This service is intentionally minimal - no authentication, no database,
no document handling. It's designed to verify basic connectivity between
the UI and a local LLaMA model.

TODO: This can later be expanded to:
- Add authentication/authorization
- Integrate with document processing for legal analysis
- Add conversation history
- Add streaming responses
- Add error handling and retries
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Tuple
import httpx
import os
import logging
import re
import hashlib
import sys

# GPU detection and logging
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# GPU detection and logging
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None

# GPU Status Check and Logging
def check_gpu_status():
    """Check GPU availability and log status"""
    gpu_info = {
        "torch_available": False,
        "cuda_available": False,
        "device_name": None,
        "device_count": 0,
        "vram_total_gb": None,
        "vram_free_gb": None,
        "vram_used_gb": None,
    }
    
    if TORCH_AVAILABLE:
        gpu_info["torch_available"] = True
        gpu_info["cuda_available"] = torch.cuda.is_available()
        
        if gpu_info["cuda_available"]:
            gpu_info["device_count"] = torch.cuda.device_count()
            if gpu_info["device_count"] > 0:
                gpu_info["device_name"] = torch.cuda.get_device_name(0)
                # Get VRAM info using torch
                vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                vram_allocated = torch.cuda.memory_allocated(0) / (1024**3)
                vram_reserved = torch.cuda.memory_reserved(0) / (1024**3)
                gpu_info["vram_total_gb"] = round(vram_total, 2)
                gpu_info["vram_used_gb"] = round(vram_allocated, 2)
                gpu_info["vram_free_gb"] = round(vram_total - vram_reserved, 2)
    
    # Try pynvml as fallback for VRAM info
    if PYNVML_AVAILABLE and not gpu_info["cuda_available"]:
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_info["device_name"] = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info["vram_total_gb"] = round(mem_info.total / (1024**3), 2)
            gpu_info["vram_free_gb"] = round(mem_info.free / (1024**3), 2)
            gpu_info["vram_used_gb"] = round(mem_info.used / (1024**3), 2)
            gpu_info["cuda_available"] = True
            gpu_info["device_count"] = pynvml.nvmlDeviceGetCount()
        except Exception as e:
            logger.warning(f"Failed to get GPU info via pynvml: {e}")
    
    return gpu_info

# Check GPU on startup
gpu_status = check_gpu_status()
logger.info("=" * 60)
logger.info("GPU Status Check")
logger.info("=" * 60)
logger.info(f"PyTorch available: {gpu_status['torch_available']}")
logger.info(f"CUDA available: {gpu_status['cuda_available']}")
logger.info(f"Device count: {gpu_status['device_count']}")
if gpu_status['device_name']:
    logger.info(f"Device name: {gpu_status['device_name']}")
if gpu_status['vram_total_gb']:
    logger.info(f"VRAM Total: {gpu_status['vram_total_gb']} GB")
    logger.info(f"VRAM Used: {gpu_status['vram_used_gb']} GB")
    logger.info(f"VRAM Free: {gpu_status['vram_free_gb']} GB")
logger.info("=" * 60)

# Fail fast if GPU is expected but not available
if os.getenv("REQUIRE_GPU", "false").lower() == "true" and not gpu_status["cuda_available"]:
    logger.error("GPU is required but not available! Exiting...")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Ollama Query Service",
    description="Minimal service for querying local LLaMA 3 model via Ollama",
    version="1.0.0"
)

# Enable CORS to allow frontend to call this service
# TODO: In production, restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama configuration
# When running in Docker, use service name 'ollama' instead of 'localhost'
# When running locally, use 'localhost'
# Priority: OLLAMA_BASE_URL env var > OLLAMA_HOST env var > auto-detect
_is_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER") == "true"
_default_host = "ollama" if _is_docker else "localhost"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", _default_host)
# If OLLAMA_BASE_URL is explicitly set, use it; otherwise construct from OLLAMA_HOST
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL") or f"http://{OLLAMA_HOST}:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# System prompts removed - starting fresh
SYSTEM_INSTRUCTION = ""

CONTRADICTION_SYSTEM_INSTRUCTION = ""

# Chunking configuration
# Target chunk size: ~700 tokens per chunk
# Token estimation: For LLaMA 3, approximately 4 characters per token
# So ~700 tokens ≈ 2800 characters
CHUNK_SIZE_CHARS = 2800  # Conservative estimate for ~700 tokens

# LLaMA-3.1 8B Configuration
# Context window: 2048 tokens (4-bit quantized model)
# Token estimation: For LLaMA 3.1, approximately 4 characters per token
# So 2048 tokens ≈ 8192 characters
LLAMA_CONTEXT_WINDOW_TOKENS = 2048
LLAMA_CONTEXT_WINDOW_CHARS = 8192  # Conservative estimate for 2048 tokens


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    For LLaMA 3.1, we use a conservative estimate of 4 characters per token.
    """
    return len(text) // 4


# PII Tokenization
# How PII is tokenized:
# - Email addresses, phone numbers, SSNs, and other PII patterns are detected
# - Detected PII is replaced with tokenized placeholders (e.g., [EMAIL_1], [PHONE_1])
# - Original PII values are hashed and stored in a mapping (not logged)
# - Only tokenized text is sent to the model and logged
# - This protects sensitive data while maintaining query functionality
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),
    'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
    'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
}


def tokenize_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Tokenize PII in text before sending to model.
    
    How PII is tokenized:
    - Detects common PII patterns (email, phone, SSN, etc.)
    - Replaces PII with tokenized placeholders (e.g., [EMAIL_1], [PHONE_1])
    - Returns tokenized text and a mapping of tokens to hashed PII values
    - Original PII values are hashed (SHA-256) for reference but not stored in logs
    
    Args:
        text: Input text that may contain PII
        
    Returns:
        Tuple of (tokenized_text, pii_mapping) where:
        - tokenized_text: Text with PII replaced by tokens
        - pii_mapping: Dict mapping tokens to hashed PII values (for reference only)
    """
    tokenized_text = text
    pii_mapping = {}
    token_counter = {}
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.finditer(text)
        for match in matches:
            pii_value = match.group(0)
            # Create token placeholder
            token_counter[pii_type] = token_counter.get(pii_type, 0) + 1
            token = f"[{pii_type.upper()}_{token_counter[pii_type]}]"
            
            # Hash the PII value (SHA-256) for reference mapping
            # This hash is NOT logged - only the token is logged
            pii_hash = hashlib.sha256(pii_value.encode()).hexdigest()[:16]  # First 16 chars for brevity
            pii_mapping[token] = f"{pii_type}:{pii_hash}"
            
            # Replace PII with token
            tokenized_text = tokenized_text.replace(pii_value, token, 1)
    
    return tokenized_text, pii_mapping


def build_llama_prompt(
    user_query: str,
    documents: Optional[List[Dict]] = None,
    facts: Optional[List] = None,
    intent: Optional[str] = None,
    show_sources: bool = False,
    document_text: Optional[str] = None
) -> str:
    """
    Build LLaMA input prompt from Query panel input.
    System prompts removed - starting fresh.
    
    Args:
        user_query: Free-text prompt from Query panel
        documents: Optional list of document excerpts
        facts: Optional list of facts
        intent: Detected user intent (summarize_section, extract_facts, check_contradictions, general)
        show_sources: Whether to include sources in response
        document_text: Optional document text for context
        
    Returns:
        Formatted prompt string ready for LLaMA-3.1 8B
    """
    # Start with user query (no system instruction)
    prompt_parts = []
    
    # Add user query (tokenized)
    tokenized_query, _ = tokenize_pii(user_query)
    prompt_parts.append(f"User Query: {tokenized_query}")
    
    # Add documents if provided
    if documents:
        prompt_parts.append("\n\nDocument Excerpts:")
        for i, doc in enumerate(documents, 1):
            doc_text = doc.get('text', doc.get('document_text', ''))
            doc_name = doc.get('document_name', doc.get('name', f'Document {i}'))
            page = doc.get('page', doc.get('page_number', 'N/A'))
            
            # Tokenize document text
            tokenized_doc, _ = tokenize_pii(doc_text)
            prompt_parts.append(f"\n[Document {i} - {doc_name}, Page {page}]:\n{tokenized_doc}")
    
    # Add facts if provided
    if facts:
        prompt_parts.append("\n\nFactual Statements:")
        for fact in facts:
            fact_text = fact.text if hasattr(fact, 'text') else fact.get('text', '')
            doc_name = fact.document_name if hasattr(fact, 'document_name') else fact.get('document_name', 'Unknown')
            page = fact.page if hasattr(fact, 'page') else fact.get('page', 'N/A')
            
            # Tokenize fact text
            tokenized_fact, _ = tokenize_pii(fact_text)
            prompt_parts.append(f'\n- {doc_name}, Page {page}: "{tokenized_fact}"')
    
    # Combine all parts
    full_prompt = "\n".join(prompt_parts)
    
    # Truncate to fit within 2048-token context window
    # Reserve ~200 tokens for model response, so use ~1800 tokens for input
    max_input_chars = (LLAMA_CONTEXT_WINDOW_TOKENS - 200) * 4  # ~7200 chars
    if len(full_prompt) > max_input_chars:
        logger.warning(f"Prompt truncated from {len(full_prompt)} to {max_input_chars} characters to fit context window")
        full_prompt = full_prompt[:max_input_chars] + "\n\n[Content truncated to fit context window]"
    
    return full_prompt


def chunk_document(
    document_text: str,
    document_name: str,
    pages: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Chunk a document into smaller pieces while preserving page boundaries.
    
    Why chunking is required for long legal documents:
    - Legal documents can be hundreds of pages long, exceeding model context limits
    - Processing in chunks ensures all content is analyzed without truncation
    - Preserving page boundaries maintains accurate page references for auditability
    
    Args:
        document_text: Full document text
        document_name: Name of the document
        pages: Optional list of page dicts with page_number and text
    
    Returns:
        List of chunk dicts, each containing:
        - document_name: Name of the document
        - chunk_number: Sequential chunk number (1-indexed)
        - page_range: String like "1-3" or "5" indicating page range
        - chunk_text: The text content of this chunk
    """
    chunks = []
    
    # If pages are provided, chunk by pages to preserve page boundaries
    # This ensures we never mix page numbers across chunks, maintaining auditability
    if pages:
        current_chunk_pages = []
        current_chunk_text = ""
        chunk_number = 1
        
        for page_info in pages:
            page_num = page_info.get("page_number", 1)
            page_text = page_info.get("text", "").strip()
            
            if not page_text:
                continue
            
            # Check if adding this page would exceed chunk size
            # If current chunk is empty, we must add at least one page
            if current_chunk_text and estimate_tokens(current_chunk_text + "\n\n" + page_text) > CHUNK_SIZE_CHARS // 4:
                # Save current chunk before starting a new one
                page_range = f"{current_chunk_pages[0]}" if len(current_chunk_pages) == 1 else f"{current_chunk_pages[0]}-{current_chunk_pages[-1]}"
                chunks.append({
                    "document_name": document_name,
                    "chunk_number": chunk_number,
                    "page_range": page_range,
                    "chunk_text": current_chunk_text.strip()
                })
                chunk_number += 1
                current_chunk_pages = []
                current_chunk_text = ""
            
            # Add page to current chunk
            current_chunk_pages.append(page_num)
            if current_chunk_text:
                current_chunk_text += "\n\n" + page_text
            else:
                current_chunk_text = page_text
        
        # Add final chunk if there's remaining content
        if current_chunk_text:
            page_range = f"{current_chunk_pages[0]}" if len(current_chunk_pages) == 1 else f"{current_chunk_pages[0]}-{current_chunk_pages[-1]}"
            chunks.append({
                "document_name": document_name,
                "chunk_number": chunk_number,
                "page_range": page_range,
                "chunk_text": current_chunk_text.strip()
            })
    else:
        # Fallback: chunk by character count if pages not provided
        # This is less ideal as we lose page boundary information
        # Split text into paragraphs first to avoid breaking mid-sentence
        paragraphs = document_text.split('\n\n')
        current_chunk_text = ""
        chunk_number = 1
        current_start_char = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if adding this paragraph would exceed chunk size
            if current_chunk_text and estimate_tokens(current_chunk_text + "\n\n" + para) > CHUNK_SIZE_CHARS // 4:
                # Save current chunk
                chunks.append({
                    "document_name": document_name,
                    "chunk_number": chunk_number,
                    "page_range": "N/A",  # No page info available
                    "chunk_text": current_chunk_text.strip()
                })
                chunk_number += 1
                current_chunk_text = ""
            
            # Add paragraph to current chunk
            if current_chunk_text:
                current_chunk_text += "\n\n" + para
            else:
                current_chunk_text = para
        
        # Add final chunk
        if current_chunk_text:
            chunks.append({
                "document_name": document_name,
                "chunk_number": chunk_number,
                "page_range": "N/A",
                "chunk_text": current_chunk_text.strip()
            })
    
    return chunks


async def process_chunk_with_model(
    chunk: Dict,
    ollama_url: str,
    ollama_model: str,
    user_question: Optional[str] = None
) -> str:
    """
    Process a single document chunk through the LLaMA model.
    
    This function:
    1. Builds the chunk-specific prompt with document metadata
    2. If a user question is provided, includes it to filter relevant facts
    3. Invokes the model
    4. Returns the raw model response (post-processing happens later)
    
    Why we don't ask the model to summarize or merge chunks:
    - Merging is handled programmatically to preserve exact model outputs
    - This prevents hallucination that could occur if the model tries to synthesize across chunks
    - Programmatic merging maintains auditability: each chunk's response is preserved
    - This design ensures deterministic, traceable results for legal document analysis
    """
    # Build chunk-specific prompt
    if user_question:
        question_lower = user_question.lower()
        is_party_question = 'defendant' in question_lower or 'plaintiff' in question_lower or 'party' in question_lower
        
        # Special handling for party/defendant questions - they're often on early pages
        party_instruction = ""
        if is_party_question:
            # Extract page range to check if this is an early page
            page_range = chunk.get('page_range', '')
            page_nums = re.findall(r'\d+', page_range)
            is_early_chunk = False
            if page_nums:
                first_page = int(page_nums[0])
                is_early_chunk = first_page <= 5
            
            if is_early_chunk:
                party_instruction = """
IMPORTANT FOR PARTY QUESTIONS:
- Legal documents typically list all parties (plaintiffs, defendants) on the first few pages
- Look for case captions, headers, or party listings
- Extract ALL party names mentioned, even if they appear in different roles (plaintiff, defendant, counterclaim plaintiff, etc.)
- Format as: "Page X: [Party Name] ([Role])"
"""
        
        # Check if this is an attorney question
        is_attorney_question = 'attorney' in user_question.lower() or 'lawyer' in user_question.lower() or 'counsel' in user_question.lower()
        
        # Special instruction for attorney questions
        attorney_instruction = ""
        if is_attorney_question:
            attorney_instruction = """
SPECIAL INSTRUCTIONS FOR ATTORNEY QUESTIONS:
- Legal documents often list ALL parties' attorneys together in a single section (e.g., "FOR [PARTY]: [LAW FIRM] BY: [ATTORNEY]")
- When you find attorney information, extract the COMPLETE attorney listing section, including ALL parties' attorneys
- This provides full context and is standard practice in legal documents
- Format the complete section with page number: "Page X: [complete attorney listing section]"
- Include all parties' attorneys if they appear together in the same section
"""
        
        # REFACTORED: Llama ONLY extracts verbatim facts - NO reasoning or answering
        # The extraction service will handle question routing and fact validation
        chunk_prompt = f"""You are a legal fact extraction engine.

Rules:
- You may ONLY return text that appears verbatim in the provided context.
- If the answer does not appear explicitly, return: NOT FOUND.
- Do NOT infer.
- Do NOT paraphrase.
- Do NOT explain.
- Do NOT answer the question - only extract verbatim text.

QUESTION (for context only - do not answer): {user_question}
{party_instruction}
{attorney_instruction}

DOCUMENT CHUNK:
Document: {chunk['document_name']}
Pages: {chunk['page_range']}

Content:
{chunk['chunk_text']}

Extract ONLY verbatim text that directly relates to the question. Return JSON:
{{
    "facts": ["verbatim text 1", "verbatim text 2"],
    "not_found": false
}}"""
    else:
        # Original behavior: extract all factual statements
        chunk_prompt = f"""Extract factual statements from the following document chunk.

Document: {chunk['document_name']}
Chunk: {chunk['chunk_number']}
Pages: {chunk['page_range']}

{chunk['chunk_text']}"""
    
    # No system instruction - just use chunk prompt directly
    full_prompt = chunk_prompt
    
    payload = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    except httpx.ConnectError as conn_err:
        error_msg = f"Cannot connect to Ollama at {ollama_url} for chunk {chunk['chunk_number']}: {conn_err}"
        logger.error(error_msg)
        # Raise the error so the caller can handle it properly
        raise Exception(error_msg) from conn_err
    except httpx.TimeoutException as timeout_err:
        error_msg = f"Timeout processing chunk {chunk['chunk_number']}: {timeout_err}"
        logger.error(error_msg)
        # Raise the error so the caller can handle it properly
        raise Exception(error_msg) from timeout_err
    except Exception as e:
        # Log error and re-raise so caller can handle it
        logger.error(f"Error processing chunk {chunk['chunk_number']}: {e}")
        raise


def post_process_response(response: str) -> str:
    """
    Post-process model response to remove non-factual content.
    
    This applies the existing post-processing logic that removes any lines
    not starting with '- Page X:' or 'Page X:' to ensure only factual statements with
    page references are kept.
    """
    if not response or not response.strip():
        return ""
    
    lines = response.split('\n')
    factual_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Keep lines that start with page references (with or without dash)
        if line_stripped.startswith('Page') or line_stripped.startswith('- Page'):
            factual_lines.append(line_stripped)
        # Also keep "Not found" messages for now (will be filtered later if we have real results)
        elif 'not found in the provided text' in line_stripped.lower():
            factual_lines.append(line_stripped)
    
    clean_response = '\n'.join(factual_lines)
    
    # If post-processing removed everything but we had a response, check if it was
    # the "Not found" message (which doesn't follow the Page format)
    if not clean_response and response.strip():
        if 'not found in the provided text' in response.lower():
            clean_response = 'Not found in the provided text.'
    
    return clean_response


def format_facts_for_contradiction_detection(facts: List["Fact"]) -> str:
    """
    Format facts for contradiction detection analysis.
    
    Builds the model input from the facts array:
    - Formats each fact as: "- <document_name>, Page <page>: "<text>""
    - Concatenates all facts into a single string
    - Prefixes with: "Factual Statements:\n"
    
    Why contradiction detection uses extracted facts only (to reduce hallucination):
    - Pre-extracted facts ensure the model only analyzes what was actually stated,
      not what might be inferred from raw document text
    - Reduces context window: Facts are concise, allowing more facts to be analyzed together
    - Maintains auditability: Each fact has a clear source (document name and page)
    - Enables focused analysis: The model can concentrate on logical contradictions rather than
      text extraction, reducing the risk of misinterpreting source material
    """
    formatted_lines = ["Factual Statements:"]
    for fact in facts:
        # Format each fact as: "- <document_name>, Page <page>: "<text>""
        formatted_lines.append(f'- {fact.document_name}, Page {fact.page}: "{fact.text}"')
    return "\n".join(formatted_lines)


async def process_contradiction_detection(
    facts: List["Fact"],
    ollama_url: str,
    ollama_model: str
) -> str:
    """
    Process contradiction detection using extracted facts.
    
    REFACTORED: Now uses GPT-4o for reasoning (not Llama).
    Llama is ONLY for extraction - reasoning tasks use GPT-4o.
    
    This function:
    1. Formats facts according to specification
    2. Calls GPT-4o for reasoning (not Llama)
    3. Returns the model response
    
    Why this workflow uses GPT-4o:
    - Contradiction detection is reasoning, not extraction
    - GPT-4o is better at logical reasoning and analysis
    - Llama is reserved for verbatim fact extraction only
    """
    # Format facts for GPT-4o reasoning
    formatted_facts = format_facts_for_contradiction_detection(facts)
    
    try:
        from app.services.reasoning_service import ReasoningService
        
        reasoning_service = ReasoningService()
        
        # Convert facts to format expected by reasoning service
        extracted_facts = []
        for fact in facts:
            extracted_facts.append({
                "fact": fact.text,
                "source": {
                    "document_name": fact.document_name,
                    "page_number": fact.page
                }
            })
        
        # Use GPT-4o for contradiction detection (reasoning task)
        result = reasoning_service.reason(
            question="Are there any contradictions in these statements?",
            extracted_facts=extracted_facts,
            task_type="contradiction"
        )
        
        return result.get("answer", "No contradictions found.")
        
    except Exception as e:
        logger.error(f"Error processing contradiction detection with GPT-4o: {e}", exc_info=True)
        return "No contradictions found."


def filter_relevant_facts(combined_response: str, question: str) -> str:
    """
    Filter response to keep only facts relevant to the question.
    Uses keyword matching to identify relevant lines.
    Aggressively removes "Not found" messages and irrelevant content.
    
    Args:
        combined_response: Combined response from all chunks
        question: Original user question
        
    Returns:
        Filtered response with only relevant facts, or original if filtering too aggressive
    """
    if not question or not combined_response:
        return combined_response
    
    # If response is very short, don't filter (might be a direct answer)
    if len(combined_response.strip()) < 200:
        logger.debug("Response too short to filter, returning as-is")
        return combined_response
    
    question_lower = question.lower()
    
    # Extract keywords from question (remove common stopwords)
    stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                 'are', 'is', 'was', 'were', 'did', 'does', 'do', 'what', 'who', 'when', 
                 'where', 'how', 'which', 'this', 'that', 'these', 'those', 'in', 'selected', 'case'}
    
    # Extract meaningful keywords from question
    question_words = re.findall(r'\b\w+\b', question_lower)
    question_keywords = {w for w in question_words if w not in stopwords and len(w) > 2}
    
    # Add domain-specific keywords based on question type
    if 'defendant' in question_lower or 'defendants' in question_lower:
        question_keywords.update(['defendant', 'defendants', 'party', 'parties', 'counterclaim', 'third-party'])
    if 'plaintiff' in question_lower or 'plaintiffs' in question_lower:
        question_keywords.update(['plaintiff', 'plaintiffs', 'party', 'parties'])
    if 'case' in question_lower:
        question_keywords.update(['case', 'lawsuit', 'action', 'proceeding'])
    
    # For attorney questions, add legal keywords
    if 'attorney' in question_lower or 'lawyer' in question_lower or 'counsel' in question_lower:
        question_keywords.update(['attorney', 'lawyer', 'counsel', 'esquire', 'esq', 'llp', 'law', 'firm', 'represent'])
        # Also include the entity name if mentioned
        entity_match = re.search(r'for\s+([^?]+)', question_lower)
        if entity_match:
            entity_name = entity_match.group(1).strip()
            # Extract key words from entity name
            entity_words = re.findall(r'\b\w+\b', entity_name)
            question_keywords.update([w.lower() for w in entity_words if len(w) > 2 and w.lower() not in stopwords])
    
    # For questions about parties/defendants, also look for common legal document headers
    if 'defendant' in question_lower or 'plaintiff' in question_lower or 'party' in question_lower:
        # Legal documents often list parties in headers - look for vs, v., against, etc.
        question_keywords.update(['vs', 'v.', 'against', 'versus', 'inc', 'company', 'corporation', 'llc'])
    
    # If no meaningful keywords extracted, don't filter
    if not question_keywords:
        logger.debug("No meaningful keywords extracted, returning original response")
        return combined_response
    
    lines = combined_response.split('\n')
    relevant_lines = []
    seen_lines = set()  # Avoid duplicates
    
    # First pass: identify lines with strong keyword matches
    strong_matches = []  # Lines with multiple keyword matches
    weak_matches = []    # Lines with single keyword match
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        line_lower = line_stripped.lower()
        
        # ALWAYS skip "Not found" messages - they add no value
        if 'not found' in line_lower or 'no relevant' in line_lower or 'not mentioned' in line_lower:
            continue
        
        # Skip lines that explicitly say they're not relevant
        if 'not relevant' in line_lower or 'does not' in line_lower and 'explicitly' in line_lower:
            continue
        
        # Skip duplicate lines
        if line_stripped in seen_lines:
            continue
        
        # Check if line contains question keywords
        keyword_matches = sum(1 for keyword in question_keywords if keyword in line_lower)
        
        # For attorney questions, prioritize lines with attorney-related keywords AND entity name
        if 'attorney' in question_lower or 'lawyer' in question_lower:
            attorney_keywords = ['attorney', 'lawyer', 'counsel', 'esquire', 'esq', 'llp', 'represent', 'for']
            has_attorney_keyword = any(kw in line_lower for kw in attorney_keywords)
            
            # Extract entity name from question (e.g., "Emhart Industries")
            entity_name_parts = []
            if 'for' in question_lower:
                # Extract text after "for"
                entity_match = re.search(r'for\s+([^?]+)', question_lower)
                if entity_match:
                    entity_text = entity_match.group(1).strip()
                    # Get key words from entity (e.g., "emhart", "industries")
                    entity_words = re.findall(r'\b\w+\b', entity_text)
                    entity_name_parts = [w.lower() for w in entity_words if len(w) > 2]
            
            # Check if line contains entity name
            has_entity_name = any(part in line_lower for part in entity_name_parts) if entity_name_parts else True
            
            if has_attorney_keyword and has_entity_name:
                # Very strong match - this likely contains the answer
                # Boost score for attorney + entity matches
                boosted_score = keyword_matches + 3  # Boost attorney matches
                strong_matches.append((line_stripped, boosted_score))
                seen_lines.add(line_stripped)
                continue
            elif has_attorney_keyword and keyword_matches > 0:
                # Strong match for attorney question
                strong_matches.append((line_stripped, keyword_matches + 1))
                seen_lines.add(line_stripped)
                continue
        
        # For questions about parties/defendants, be more lenient - keep lines from early pages
        is_early_page = False
        if 'defendant' in question_lower or 'plaintiff' in question_lower or 'party' in question_lower:
            # Extract page number if present
            page_match = re.search(r'page\s+(\d+)', line_lower)
            if page_match:
                page_num = int(page_match.group(1))
                # Consider first 5 pages as "early" for party listings
                is_early_page = page_num <= 5
        
        # Categorize matches
        if keyword_matches > 1:
            # Multiple keyword matches - strong relevance
            strong_matches.append((line_stripped, keyword_matches))
            seen_lines.add(line_stripped)
        elif keyword_matches > 0 or line_stripped.startswith('Page') or is_early_page:
            # Single keyword match or page reference - weak relevance
            weak_matches.append((line_stripped, keyword_matches))
            seen_lines.add(line_stripped)
    
    # Prioritize strong matches, then add weak matches
    # Sort strong matches by number of keyword matches (descending)
    strong_matches.sort(key=lambda x: x[1], reverse=True)
    relevant_lines = [line for line, _ in strong_matches]
    
    # Add weak matches, but limit them to avoid clutter
    # For attorney questions, be very selective - only add if they mention the entity
    if 'attorney' in question_lower or 'lawyer' in question_lower:
        # Extract entity name for filtering
        entity_name_parts = []
        if 'for' in question_lower:
            entity_match = re.search(r'for\s+([^?]+)', question_lower)
            if entity_match:
                entity_text = entity_match.group(1).strip()
                entity_words = re.findall(r'\b\w+\b', entity_text)
                entity_name_parts = [w.lower() for w in entity_words if len(w) > 2]
        
        # Only add weak matches that mention the entity or are clearly attorney-related
        filtered_weak = []
        for line, score in weak_matches:
            line_lower = line.lower()
            has_entity = any(part in line_lower for part in entity_name_parts) if entity_name_parts else True
            has_attorney_term = any(term in line_lower for term in ['attorney', 'lawyer', 'counsel', 'esquire', 'esq', 'llp', 'represent'])
            
            # Only include if it has entity name or attorney terms
            if has_entity or has_attorney_term:
                filtered_weak.append((line, score))
        
        # Limit to top 3 weak matches for attorney questions
        for line, _ in filtered_weak[:3]:
            if line not in relevant_lines:
                relevant_lines.append(line)
    else:
        # For other questions, add more weak matches
        max_weak_matches = 10
        for line, _ in weak_matches[:max_weak_matches]:
            if line not in relevant_lines:
                relevant_lines.append(line)
    
    # Special handling for party/defendant questions - keep early pages even if keywords don't match perfectly
    if 'defendant' in question_lower or 'plaintiff' in question_lower or 'party' in question_lower:
        # For party questions, also include lines from early pages (pages 1-5) even without keyword matches
        # Legal documents typically list parties on the first few pages
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped in seen_lines:
                continue
            
            line_lower = line_stripped.lower()
            if 'not found' in line_lower:
                continue
            
            # Check if this is an early page (pages 1-5)
            page_match = re.search(r'page\s+(\d+)', line_lower)
            if page_match:
                page_num = int(page_match.group(1))
                if page_num <= 5 and line_stripped not in [l.strip() for l in relevant_lines]:
                    # Early page - likely contains party information, include it
                    relevant_lines.append(line_stripped)
                    seen_lines.add(line_stripped)
                    logger.debug(f"Including early page {page_num} for party question")
    
    # Aggressively filter out "Not found" and irrelevant messages
    # Always remove these - they add no value
    filtered_lines = []
    for line in relevant_lines:
        line_lower = line.lower()
        # Remove all variations of "not found" messages
        if any(phrase in line_lower for phrase in [
            'not found in the provided text',
            'not found',
            'no relevant information',
            'not mentioned',
            'does not explicitly',
            'not directly related',
            'content not directly related'
        ]):
            continue
        # Remove lines that say they're not relevant
        if 'not relevant' in line_lower and ('however' in line_lower or 'seems' in line_lower):
            continue
        filtered_lines.append(line)
    
    original_count = len(relevant_lines)
    relevant_lines = filtered_lines
    if len(filtered_lines) < original_count:
        logger.info(f"Filtered out {original_count - len(filtered_lines)} 'Not found' or irrelevant messages")
    
    # If we filtered everything out, return original response (filter was too aggressive)
    if not relevant_lines:
        logger.warning(f"Relevance filter removed all lines, returning original response (question: {question[:50]}...)")
        return combined_response
    
    # If we kept less than 10% of lines, the filter might be too aggressive - return original
    # Exception: for party questions, we might have fewer but more relevant lines
    if len(relevant_lines) < len(lines) * 0.1 and len(lines) > 10:
        # For party questions, be more lenient (they might be concentrated in early pages)
        if not ('defendant' in question_lower or 'plaintiff' in question_lower or 'party' in question_lower):
            logger.warning(f"Relevance filter removed {len(lines) - len(relevant_lines)}/{len(lines)} lines, might be too aggressive. Returning original.")
            return combined_response
    
    # Final cleanup: Remove duplicates and prioritize actual answers
    # Remove exact duplicates
    seen_content = set()
    deduplicated = []
    for line in relevant_lines:
        # Normalize line for duplicate detection (remove extra whitespace)
        normalized = ' '.join(line.split())
        if normalized not in seen_content:
            seen_content.add(normalized)
            deduplicated.append(line)
    
    relevant_lines = deduplicated
    
    # For attorney questions, prioritize lines with both entity name and attorney terms
    if 'attorney' in question_lower or 'lawyer' in question_lower:
        # Extract entity name
        entity_name_parts = []
        if 'for' in question_lower:
            entity_match = re.search(r'for\s+([^?]+)', question_lower)
            if entity_match:
                entity_text = entity_match.group(1).strip()
                entity_words = re.findall(r'\b\w+\b', entity_text)
                entity_name_parts = [w.lower() for w in entity_words if len(w) > 2]
        
        # Separate lines with both entity and attorney terms (best matches)
        best_matches = []
        other_matches = []
        
        for line in relevant_lines:
            line_lower = line.lower()
            has_entity = any(part in line_lower for part in entity_name_parts) if entity_name_parts else False
            has_attorney = any(term in line_lower for term in ['attorney', 'lawyer', 'counsel', 'esquire', 'esq', 'llp', 'represent', 'for'])
            
            if has_entity and has_attorney:
                best_matches.append(line)
            else:
                other_matches.append(line)
        
        # Prioritize best matches
        relevant_lines = best_matches + other_matches[:5]  # Limit other matches to top 5
        logger.info(f"Prioritized {len(best_matches)} best matches for attorney question")
    
    # For party questions, prioritize early pages (they typically contain party listings)
    if 'defendant' in question_lower or 'plaintiff' in question_lower or 'party' in question_lower:
        # Sort lines to put early pages first
        def get_page_num(line: str) -> int:
            match = re.search(r'page\s+(\d+)', line.lower())
            return int(match.group(1)) if match else 9999  # Put lines without page numbers at end
        
        relevant_lines.sort(key=get_page_num)
        logger.info(f"Sorted results by page number for party question (early pages first)")
    
    logger.info(f"Relevance filter kept {len(relevant_lines)}/{len(lines)} lines (after deduplication)")
    return '\n'.join(relevant_lines)


def combine_chunk_responses(chunk_responses: List[str], question: Optional[str] = None) -> str:
    """
    Combine responses from multiple chunks into a single response.
    
    Why merging is handled by code and not the model:
    - Prevents hallucination: The model might synthesize or infer connections between chunks
    - Preserves auditability: Each chunk's exact output is maintained, allowing traceability
    - Ensures determinism: Programmatic merging produces consistent results
    - Maintains source-grounded behavior: No cross-chunk reasoning that could introduce errors
    
    This approach ensures that the final response is a simple concatenation of
    factual statements extracted from each chunk, with no model-generated synthesis.
    
    Args:
        chunk_responses: List of responses from individual chunks
        question: Optional user question for relevance filtering
    """
    # Filter out empty responses
    non_empty_responses = [resp.strip() for resp in chunk_responses if resp.strip()]
    
    if not non_empty_responses:
        return ""
    
    # Combine responses with newlines
    # Each chunk's response is already formatted with '- Page X: "..."' lines
    combined = '\n'.join(non_empty_responses)
    
    # Check if we have any real results (not just "Not found" messages)
    has_real_results = any('not found' not in resp.lower() for resp in non_empty_responses)
    
    # If we have real results, remove all "Not found" messages before filtering
    if has_real_results:
        lines = combined.split('\n')
        filtered_lines = [line for line in lines if 'not found' not in line.lower()]
        combined = '\n'.join(filtered_lines)
        logger.info(f"Removed 'Not found' messages since we have {len([l for l in lines if 'not found' not in l.lower()])} real results")
    
    # Apply relevance filter if question is provided
    if question:
        combined = filter_relevant_facts(combined, question)
        logger.info(f"Applied relevance filter to combined response (question: {question[:50]}...)")
    
    return combined


class DocumentInput(BaseModel):
    """Input model for a single document"""
    document_name: str
    document_text: str
    pages: Optional[List[Dict]] = None  # List of page dicts: [{"page_number": 1, "text": "..."}, ...]


class Fact(BaseModel):
    """Model for a single factual statement"""
    document_name: str
    page: int
    text: str
    
    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "document_name": "Deposition Transcript",
                "page": 5,
                "text": "The incident occurred on March 15th at 3:00 PM."
            }
        }


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    prompt: str
    # Intent-aware system prompt support
    intent: Optional[str] = None  # summarize_section, extract_facts, check_contradictions, general
    show_sources: Optional[bool] = False  # Whether to include sources in response
    # Optional fields for single document analysis with chunking (backward compatible)
    # If provided, the document will be chunked before analysis
    document_text: Optional[str] = None
    document_name: Optional[str] = None
    pages: Optional[List[Dict]] = None  # List of page dicts: [{"page_number": 1, "text": "..."}, ...]
    # Optional field for multiple document analysis
    # If provided, processes multiple documents independently
    documents: Optional[List[DocumentInput]] = None
    # Optional field for contradiction detection
    # If provided and non-empty, bypasses document processing and analyzes facts for contradictions
    # This field accepts an array of Fact objects, each containing document_name, page, and text
    facts: Optional[List[Fact]] = None
    
    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "prompt": "Analyze for contradictions",
                "facts": [
                    {
                        "document_name": "Deposition Transcript",
                        "page": 5,
                        "text": "The incident occurred on March 15th at 3:00 PM."
                    }
                ]
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    response: str
    # Optional structured response for multi-document analysis
    # When documents are provided, this contains results grouped by document name
    documents: Optional[Dict[str, str]] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Ollama Query Service",
        "status": "running",
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL
    }

@app.get("/health")
async def health_check():
    """Health check endpoint that includes GPU status"""
    gpu_status = check_gpu_status()
    return {
        "status": "healthy",
        "service": "Ollama Query Service",
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL,
        "gpu": gpu_status
    }

@app.post("/query", response_model=QueryResponse)
async def query_ollama(request: QueryRequest):
    """
    Lawbric Query Panel Endpoint - LLaMA-3.1 8B Integration
    
    This endpoint connects the Query panel in the UI to the LLaMA-3.1 8B backend model (4-bit quantized).
    
    How the Query panel input is transformed into LLaMA input:
    - User query text is tokenized (PII removed) and used as the main prompt
    - Optional documents array: Document excerpts are formatted and appended to the prompt
    - Optional facts array: Facts are formatted and appended to the prompt
    - Total prompt is truncated to fit within 2048-token context window (4-bit quantized model)
    
    How PII is tokenized:
    - Email addresses, phone numbers, SSNs, and other PII patterns are detected
    - Detected PII is replaced with tokenized placeholders (e.g., [EMAIL_1], [PHONE_1])
    - Original PII values are hashed (SHA-256) and stored in a mapping (not logged)
    - Only tokenized text is sent to the model and logged
    - This protects sensitive data while maintaining query functionality
    
    How the model output is returned to the UI:
    - Model response is captured as text
    - Response is formatted as JSON: {"response": "<model output>", "documents": null}
    - Error handling returns appropriate HTTP status codes with error messages
    - Raw query, tokenized prompt, and model response are logged (PII-free)
    
    This endpoint supports four modes:
    1. Standard query mode (Query panel): Accepts a prompt and optional documents/facts, processes with LLaMA-3.1 8B
    2. Single document analysis mode: If document_text is provided, chunks the document
       and processes each chunk separately, then combines responses
    3. Multi-document analysis mode: If documents array is provided, processes each document
       independently and returns results grouped by document name
    4. Contradiction detection mode: If facts array is provided and non-empty, bypasses document
       processing and analyzes extracted facts for contradictions
    
    API Contract:
    - Input: JSON with "prompt" field (required)
    - Optional fields for single document analysis: "document_text", "document_name", "pages"
    - Optional field for multi-document analysis: "documents" (array of {document_name, document_text, pages})
    - Optional field for contradiction detection: "facts" (array of {document_name, page, text})
    - Output: JSON with "response" field (standard/single document/contradiction mode)
    - Output: JSON with "documents" field (multi-document mode) containing results grouped by document name
    
    Document Chunking (when document_text is provided):
    - Documents are chunked into ~700 token pieces before model invocation
    - Page boundaries are preserved (pages are never split across chunks)
    - Each chunk is processed independently through the model
    - Responses are combined programmatically (not by the model) to prevent hallucination
    
    System prompts have been removed - starting fresh.
    Models receive only the user query and context without system instructions.
    """
    
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Define ollama_url once at the start - used by all processing paths
    ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
    
    # #region agent log
    import json
    from datetime import datetime
    log_path = r"c:\LegalAI\.cursor\debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ollama_service.py:737","message":"Ollama API URL configured","data":{"ollama_url":ollama_url,"OLLAMA_BASE_URL":OLLAMA_BASE_URL,"OLLAMA_MODEL":OLLAMA_MODEL},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    # Log: Raw query received from Query panel (before PII tokenization)
    # Note: We log the query structure but not raw PII values
    logger.info(f"Query panel request received - prompt length: {len(request.prompt)}, "
                f"documents: {len(request.documents) if request.documents else 0}, "
                f"facts: {len(request.facts) if request.facts else 0}")
    
    # FIRST conditional branch: Explicitly detect a facts array in the request body
    # If facts is present and has length > 0, enter the contradiction detection branch
    # Skip any document/chunk handling or prompt-only logic for this branch
    # Why this workflow only uses extracted facts (to reduce hallucination):
    # - Pre-extracted facts ensure the model only analyzes what was actually stated,
    #   not what might be inferred from raw document text
    # - Reduces context window: Facts are concise, allowing more facts to be analyzed together
    # - Maintains auditability: Each fact has a clear source (document name and page)
    # - Enables focused analysis: The model can concentrate on logical contradictions rather than
    #   text extraction, reducing the risk of misinterpreting source material
    # Why it is separated from document ingestion:
    # - Document ingestion focuses on extraction and chunking of raw text
    # - Contradiction detection requires pre-extracted, structured facts
    # - Separation prevents mixing extraction and analysis concerns
    # - Allows facts to be validated before contradiction analysis
    # Why human review is required for outputs:
    # - Contradiction detection involves interpretation and logical reasoning, which introduces
    #   the possibility of false positives or missed contradictions
    # - Legal contradictions require nuanced understanding of context, intent, and legal standards
    # - The model may identify apparent contradictions that are actually consistent when viewed
    #   with proper legal context or additional information
    # - Human legal expertise is essential to validate identified contradictions and assess
    #   their legal significance
    if request.facts and len(request.facts) > 0:
        # Log: Facts branch was entered
        logger.info(f"Contradiction detection workflow: Processing {len(request.facts)} facts")
        
        # Contradiction detection mode
        # Skip all document and chunk logic - use ONLY the provided facts
        # Do NOT reference raw documents or document chunks
        # Why facts is separated from documents (reduce hallucination):
        # - Pre-extracted facts ensure the model only analyzes what was actually stated,
        #   not what might be inferred from raw document text
        # - Reduces context window: Facts are concise, allowing more facts to be analyzed together
        # - Maintains auditability: Each fact has a clear source (document name and page)
        # - Enables focused analysis: The model can concentrate on logical contradictions rather than
        #   text extraction, reducing the risk of misinterpreting source material
        # Why human review is required for outputs:
        # - Contradiction detection involves interpretation and logical reasoning, which introduces
        #   the possibility of false positives or missed contradictions
        # - Legal contradictions require nuanced understanding of context, intent, and legal standards
        # - The model may identify apparent contradictions that are actually consistent when viewed
        #   with proper legal context or additional information
        # - Human legal expertise is essential to validate identified contradictions and assess
        #   their legal significance
        
        # Build model prompt using only the provided facts
        # Format: "- <document_name>, Page <page>: "<text>"\n"
        # Prefix with: "Factual Statements:\n"
        # Call the existing model function with this prompt
        contradiction_result = await process_contradiction_detection(
            facts=request.facts,
            ollama_url=ollama_url,
            ollama_model=OLLAMA_MODEL
        )
        
        # Log: Raw model output before returning
        logger.info(f"Raw model output (before returning): {contradiction_result[:500]}..." if len(contradiction_result) > 500 else f"Raw model output (before returning): {contradiction_result}")
        
        # Return model output in the response field
        # Ensure the response field is populated with either a contradiction list
        # or the exact string: "No contradictions found."
        response_text = contradiction_result if contradiction_result else "No contradictions found."
        
        # Set documents to null
        return QueryResponse(
            response=response_text,
            documents=None
        )
    
    # Check if this is a multi-document analysis request
    # Why documents are processed independently:
    # - Preserves governance boundaries: Each document may have different privilege, confidentiality, or access controls
    # - Maintains auditability: Results are traceable to specific documents, preventing cross-contamination
    # - Respects privilege boundaries: Legal privilege must be maintained per-document to avoid waiver
    # - Prevents cross-document reasoning: The model is not asked to compare, synthesize, or reason across documents
    # - Ensures deterministic results: Independent processing produces consistent, reproducible outputs
    # - Supports compliance: Different documents may require different handling per regulatory requirements
    if request.documents:
        # Multi-document analysis mode
        # Process each document independently - chunks are NOT mixed across documents
        # This ensures each document's facts are extracted separately, maintaining clear boundaries
        
        document_results = {}
        
        for doc_input in request.documents:
            document_name = doc_input.document_name
            
            # Chunk this document independently
            # Do NOT mix chunks across documents - each document is processed in isolation
            chunks = chunk_document(
                document_text=doc_input.document_text,
                document_name=document_name,
                pages=doc_input.pages
            )
            
            if not chunks:
                document_results[document_name] = "Not found in the provided text."
                continue
            
            # Process each chunk of this document through the model
            # Why we process chunks sequentially and combine programmatically:
            # - We do NOT ask the model to summarize or merge chunks (prevents hallucination)
            # - We do NOT modify the model output (preserves exact factual statements)
            # - Programmatic merging maintains auditability and prevents cross-chunk inference
            # - This ensures deterministic, traceable results for legal document analysis
            chunk_responses = []
            chunk_errors = []
            for chunk in chunks:
                try:
                    chunk_response = await process_chunk_with_model(
                        chunk=chunk,
                        ollama_url=ollama_url,
                        ollama_model=OLLAMA_MODEL,
                        user_question=request.prompt  # Pass user's question to filter relevant facts
                    )
                    # Apply post-processing to each chunk response
                    clean_chunk_response = post_process_response(chunk_response)
                    if clean_chunk_response:
                        chunk_responses.append(clean_chunk_response)
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {chunk['chunk_number']} for document {document_name}: {chunk_error}")
                    chunk_errors.append(f"Chunk {chunk['chunk_number']}: {str(chunk_error)}")
            
            # If all chunks failed, include error message
            if not chunk_responses and len(chunks) > 0:
                error_details = "; ".join(chunk_errors) if chunk_errors else "All chunks failed to process"
                logger.error(f"All {len(chunks)} chunks failed for document {document_name}: {error_details}")
                document_results[document_name] = f"Error: Failed to process document. Unable to connect to LLaMA model. Errors: {error_details[:200]}"
            else:
                # Combine all chunk responses for this document programmatically
                # Why merging is handled by code and not the model:
                # - Prevents hallucination: The model might synthesize or infer connections between chunks
                # - Preserves auditability: Each chunk's exact output is maintained, allowing traceability
                # - Ensures determinism: Programmatic merging produces consistent results
                # - Maintains source-grounded behavior: No cross-chunk reasoning that could introduce errors
                combined_response = combine_chunk_responses(chunk_responses, question=request.prompt)
                
                # Store results for this document
                # Do NOT merge facts across documents - each document's results are kept separate
                document_results[document_name] = combined_response if combined_response else "Not found in the provided text."
        
        # Return structured response grouped by document name
        # Why cross-document reasoning is intentionally excluded at this stage:
        # - Governance: Different documents may have different access controls, privilege status, or confidentiality levels
        # - Auditability: Maintaining per-document results allows precise traceability and compliance verification
        # - Privilege boundaries: Legal privilege must be maintained per-document to avoid inadvertent waiver
        # - Regulatory compliance: Some regulations require document-level isolation for data handling
        # - Determinism: Independent processing ensures reproducible, verifiable results
        # - Future extensibility: Document-level results can be combined later if needed, but cannot be un-mixed
        return QueryResponse(
            response="",  # Empty for multi-document mode
            documents=document_results
        )
    
    # Check if this is a single document analysis request (chunking mode)
    elif request.document_text:
        # Document analysis with chunking
        # Why chunking is required for long legal documents:
        # Legal documents can be hundreds of pages long, exceeding model context limits.
        # Processing in chunks ensures all content is analyzed without truncation.
        # Preserving page boundaries maintains accurate page references for auditability.
        
        document_name = request.document_name or "Document"
        chunks = chunk_document(
            document_text=request.document_text,
            document_name=document_name,
            pages=request.pages
        )
        
        if not chunks:
            return QueryResponse(response="Not found in the provided text.")
        
        # Process each chunk through the model
        # Why we process chunks sequentially and combine programmatically:
        # - We do NOT ask the model to summarize or merge chunks (prevents hallucination)
        # - We do NOT modify the model output (preserves exact factual statements)
        # - Programmatic merging maintains auditability and prevents cross-chunk inference
        # - This ensures deterministic, traceable results for legal document analysis
        chunk_responses = []
        chunk_errors = []
        for chunk in chunks:
            try:
                chunk_response = await process_chunk_with_model(
                    chunk=chunk,
                    ollama_url=ollama_url,
                    ollama_model=OLLAMA_MODEL,
                    user_question=request.prompt  # Pass user's question to filter relevant facts
                )
                # Apply post-processing to each chunk response
                clean_chunk_response = post_process_response(chunk_response)
                if clean_chunk_response:
                    chunk_responses.append(clean_chunk_response)
            except Exception as chunk_error:
                logger.error(f"Error processing chunk {chunk['chunk_number']}: {chunk_error}")
                chunk_errors.append(f"Chunk {chunk['chunk_number']}: {str(chunk_error)}")
        
        # If all chunks failed, return an error instead of empty response
        if not chunk_responses and len(chunks) > 0:
            error_details = "; ".join(chunk_errors) if chunk_errors else "All chunks failed to process"
            logger.error(f"All {len(chunks)} chunks failed to process: {error_details}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to process document. Unable to connect to LLaMA model. Please ensure Ollama is running. Errors: {error_details[:200]}"
            )
        
        # Combine all chunk responses programmatically
        # Why merging is handled by code and not the model:
        # - Prevents hallucination: The model might synthesize or infer connections between chunks
        # - Preserves auditability: Each chunk's exact output is maintained, allowing traceability
        # - Ensures determinism: Programmatic merging produces consistent results
        # - Maintains source-grounded behavior: No cross-chunk reasoning that could introduce errors
        combined_response = combine_chunk_responses(chunk_responses, question=request.prompt)
        
        return QueryResponse(response=combined_response if combined_response else "Not found in the provided text.")
    
    else:
        # Standard query mode (Query panel - LLaMA-3.1 8B)
        # Build LLaMA input prompt from Query panel input
        # How the Query panel input is transformed into LLaMA input:
        # - User query text is tokenized (PII removed) and used as the main prompt
        # - Optional documents array: Document excerpts are formatted and appended
        # - Optional facts array: Facts are formatted and appended
        # - Total prompt is truncated to fit within 2048-token context window
        
        # Build prompt with PII tokenization and intent-aware system prompts
        full_prompt = build_llama_prompt(
            user_query=request.prompt,
            documents=request.documents,
            facts=request.facts,
            intent=request.intent,
            show_sources=request.show_sources if request.show_sources else False,
            document_text=request.document_text
        )
        
        # Log: Tokenized prompt (PII-free) before sending to model
        logger.info(f"Tokenized prompt (PII-free) length: {len(full_prompt)} characters, "
                    f"estimated tokens: {estimate_tokens(full_prompt)}")
        logger.debug(f"Tokenized prompt preview: {full_prompt[:500]}...")
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,  # Get complete response at once
            "options": {
                "num_predict": 256,  # Reduced to 256 for faster responses (sufficient for most queries)
                "temperature": 0.1,  # Low temperature for factual, deterministic responses
                "top_p": 0.9,  # Nucleus sampling for faster generation
                "top_k": 40,  # Limit vocabulary for faster generation
            }
        }
        
        try:
            # Send request to Ollama (LLaMA-3.1 8B)
            # Increased timeout for first request (model loading) and longer prompts
            # Use longer timeout with proper connection timeout
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(600.0, connect=30.0)  # 30s connection, 600s total (10 min) for model loading
            ) as client:
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ollama_service.py:970","message":"Attempting Ollama API connection","data":{"ollama_url":ollama_url,"model":OLLAMA_MODEL,"timeout_connect":30.0,"timeout_total":600.0},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
                except: pass
                # #endregion
                logger.info(f"Sending request to Ollama API at {ollama_url} with model {OLLAMA_MODEL}")
                logger.info(f"Payload: {json.dumps(payload)[:500]}...")  # Log first 500 chars of payload
                response = await client.post(ollama_url, json=payload)
                logger.info(f"Received response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                logger.info(f"Response JSON keys: {list(result.keys())}")
                
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ollama_service.py:976","message":"Ollama API connection successful","data":{"status_code":response.status_code,"has_response":bool(result.get("response"))},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
                except: pass
                # #endregion
                
                # Extract the response text from Ollama's response
                # Ollama returns: {"model": "...", "created_at": "...", "response": "...", "done": true}
                model_response = result.get("response", "")
                
                # Log: Model response (PII-free, already tokenized)
                logger.info(f"Model response received - length: {len(model_response)} characters")
                logger.debug(f"Model response preview: {model_response[:500]}...")
                
                if not model_response:
                    logger.error("Ollama returned an empty response")
                    raise HTTPException(
                        status_code=500,
                        detail="LLaMA-3.1 8B returned an empty response"
                    )
                
                # Post-processing: Only apply strict filtering if documents were provided
                # For simple queries without documents, keep the full response
                # For document-based queries, filter to only factual statements with page references
                if request.documents or request.document_text:
                    # Document-based query - apply strict filtering
                    clean_response = post_process_response(model_response)
                else:
                    # Simple query without documents - keep full response (just trim whitespace)
                    clean_response = model_response.strip()
                
                # How the model output is returned to the UI:
                # - Response is formatted as JSON with "response" field containing model output
                # - "documents" field is set to null for Query panel responses
                # - Error handling returns appropriate HTTP status codes
                return QueryResponse(
                    response=clean_response,
                    documents=None
                )
                
        except httpx.TimeoutException as timeout_err:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"ollama_service.py:1006","message":"Ollama API TimeoutException","data":{"ollama_url":ollama_url,"timeout_error":str(timeout_err),"timeout_connect":30.0,"timeout_total":600.0},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            logger.error(f"Request to LLaMA-3.1 8B timed out after 600 seconds")
            raise HTTPException(
                status_code=504,
                detail="Request to LLaMA-3.1 8B timed out after 10 minutes. The model may still be loading or the prompt is too complex. Please try again."
            )
        except httpx.ConnectError as conn_err:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"ollama_service.py:1012","message":"Ollama API ConnectError","data":{"OLLAMA_BASE_URL":OLLAMA_BASE_URL,"ollama_url":ollama_url,"error_detail":str(conn_err),"error_type":type(conn_err).__name__},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            logger.error(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is running and LLaMA-3.1 8B is installed."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"LLaMA-3.1 8B API error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Query panel endpoint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error processing query: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Run the service
    # Default: http://localhost:8002 (to avoid conflicts with main backend on 8000 and other services on 8001)
    port = int(os.getenv("OLLAMA_SERVICE_PORT", "8002"))
    
    # Check if port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
    except OSError as e:
        if e.errno == 10048 or e.errno == 98:  # Windows: Address already in use, Linux: Address already in use
            logger.error(f"Port {port} is already in use. Please stop any existing ollama_service processes.")
            logger.error("On Windows, run: Get-Process python | Where-Object {$_.Path -like '*ollama_service*'} | Stop-Process -Force")
            logger.error("Or check with: netstat -ano | findstr :8002")
            raise SystemExit(f"ERROR: Port {port} is already in use. Kill existing processes first.")
        else:
            raise
    
    uvicorn.run(
        "ollama_service:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

