from typing import List, Dict, Any, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from langchain_community.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from privacy.privacy_manager import PrivacyManager

class PDFReader:
    """Tool for reading and analyzing PDF documents."""
    
    def __init__(self, privacy_manager: PrivacyManager):
        """Initialize PDF reader with privacy manager."""
        self.privacy_manager = privacy_manager
        self.embeddings = OllamaEmbeddings(model="llama2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
    def read_pdf(self, file_path: str) -> str:
        """
        Read a PDF file and return its content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            str: Content of the PDF file
        """
        if self.privacy_manager.is_sensitive_data("documents"):
            if not self.privacy_manager.ask_permission("read", "PDF document"):
                return ""
                
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
            
        reader = PdfReader(file_path)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
            
        if self.privacy_manager.is_sensitive_data("documents"):
            # Store encrypted version
            encrypted = self.privacy_manager.encrypt_data(text)
            cache_path = pdf_path.with_suffix(".cache")
            cache_path.write_bytes(encrypted)
            
        return text
        
    def analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a PDF file and return metadata and statistics.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            dict: Analysis results including metadata and statistics
        """
        reader = PdfReader(file_path)
        
        # Extract metadata and basic statistics
        info = reader.metadata
        stats = {
            "num_pages": len(reader.pages),
            "file_size": Path(file_path).stat().st_size,
            "title": info.get("/Title", "Untitled"),
            "author": info.get("/Author", "Unknown"),
            "creation_date": info.get("/CreationDate", "Unknown"),
        }
        
        return stats
        
    def search_pdf(self, file_path: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for content in a PDF file using semantic search.
        
        Args:
            file_path: Path to the PDF file
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            list: List of relevant text chunks with page numbers
        """
        text = self.read_pdf(file_path)
        chunks = self.text_splitter.split_text(text)
        
        # Create vector store
        db = Chroma.from_texts(
            chunks,
            self.embeddings,
            metadatas=[{"source": file_path} for _ in chunks]
        )
        
        # Perform semantic search
        results = db.similarity_search_with_score(query, k=top_k)
        
        return [{
            "text": result[0].page_content,
            "score": result[1],
            "source": result[0].metadata["source"]
        } for result in results]
        
    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            list: List of extracted tables with metadata
        """
        # TODO: Implement table extraction using a library like tabula-py
        # For now, return empty list
        return []