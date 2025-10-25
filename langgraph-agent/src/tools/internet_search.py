import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

class InternetSearchTool:
    """Tool for searching the internet and retrieving real-time information."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """Initialize search tool with caching."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.session = requests.Session()
        
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        safe_filename = "".join(c if c.isalnum() else "_" for c in url)[:100]
        return self.cache_dir / f"{safe_filename}.json"
        
    def _cache_response(self, url: str, data: dict) -> None:
        """Cache response data for a URL."""
        cache_path = self._get_cache_path(url)
        data["timestamp"] = time.time()
        with cache_path.open("w") as f:
            json.dump(data, f)
            
    def _get_cached_response(self, url: str, max_age: int = 3600) -> Optional[dict]:
        """Get cached response if available and not expired."""
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            with cache_path.open() as f:
                data = json.load(f)
                age = time.time() - data["timestamp"]
                if age < max_age:
                    return data
        return None
        
    def search_url(self, url: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch and parse content from a specific URL.
        
        Args:
            url: URL to fetch
            use_cache: Whether to use cached results
            
        Returns:
            dict: Parsed content with metadata
        """
        if use_cache:
            cached = self._get_cached_response(url)
            if cached:
                return cached
                
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract main content
            content = {
                "title": soup.title.string if soup.title else "",
                "text": soup.get_text(),
                "links": [
                    {"text": a.get_text(), "href": urljoin(url, a.get("href", ""))}
                    for a in soup.find_all("a", href=True)
                ],
                "metadata": {
                    "url": url,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                }
            }
            
            if use_cache:
                self._cache_response(url, content)
                
            return content
            
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return {}
            
    def extract_text_by_selector(self, url: str, selector: str) -> List[str]:
        """
        Extract text from specific elements on a webpage.
        
        Args:
            url: URL to fetch
            selector: CSS selector to find elements
            
        Returns:
            list: Extracted text from matching elements
        """
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.select(selector)
            
            return [element.get_text(strip=True) for element in elements]
            
        except Exception as e:
            print(f"Error extracting text from {url}: {e}")
            return []
            
    def search_multiple_pages(
        self,
        urls: List[str],
        common_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search multiple pages and optionally extract specific content.
        
        Args:
            urls: List of URLs to search
            common_selector: Optional CSS selector to extract specific content
            
        Returns:
            list: Results from each URL
        """
        results = []
        
        for url in urls:
            content = self.search_url(url)
            
            if common_selector and content:
                content["extracted"] = self.extract_text_by_selector(url, common_selector)
                
            results.append(content)
            
        return results
        
    def is_url_safe(self, url: str) -> bool:
        """
        Check if a URL appears safe to visit.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL appears safe, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Basic checks
            if not parsed.scheme in ("http", "https"):
                return False
                
            # Add additional safety checks as needed
            return True
            
        except Exception:
            return False