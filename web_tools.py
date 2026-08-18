import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def extract_urls(text: str) -> List[str]:
    """Extract all URLs from a text prompt."""
    url_pattern = r'https?://[^\s<>"\')]+'
    return re.findall(url_pattern, text)

def fetch_url_content(url: str, max_chars: int = 5000) -> Dict[str, str]:
    """
    Fetches real-time webpage content and extracts clean readable text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='replace')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts, styles, navs
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.extract()
                
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            text = soup.get_text(separator="\n", strip=True)
            
            # Normalize excessive newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n[... Truncated, total length was {len(text)} characters]"
                
            return {
                "title": title,
                "url": url,
                "content": text,
                "status": "success"
            }
    except Exception as e:
        return {
            "title": url,
            "url": url,
            "content": f"Failed to fetch content from {url}: {str(e)}",
            "status": "error"
        }

def search_duckduckgo(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """
    Performs a real-time web search via DuckDuckGo Lite / HTML.
    """
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='replace')
            soup = BeautifulSoup(html, 'html.parser')
            
            results = []
            for item in soup.find_all('div', class_='result'):
                title_elem = item.find('a', class_='result__a')
                snippet_elem = item.find('a', class_='result__snippet')
                url_elem = item.find('a', class_='result__url')
                
                if title_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    
                    # DuckDuckGo wraps URLs in uddg query param
                    if "uddg=" in href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        actual_url = parsed.get("uddg", [href])[0]
                    else:
                        actual_url = href
                        
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": actual_url
                    })
                    if len(results) >= max_results:
                        break
            return results
    except Exception:
        return []

def get_web_context_for_prompt(prompt: str, web_search_enabled: bool = True) -> Tuple[str, List[str]]:
    """
    Scans the prompt for URLs or explicit web search requests and retrieves real-time context.
    """
    urls = extract_urls(prompt)
    sources = []
    context_blocks = []

    # 1. Fetch URLs present in prompt
    for url in urls[:3]:
        fetched = fetch_url_content(url)
        if fetched["status"] == "success":
            sources.append(f"{fetched['title']} ({url})")
            context_blocks.append(f"--- Live Web Page: {fetched['title']} ({url}) ---\n{fetched['content']}")

    # 2. Check for explicit search triggers
    clean_lower = prompt.lower()
    search_keywords = ["search web for", "search the web for", "google for", "look up online", "search for latest", "search internet for", "browse the web for", "who is", "latest news on", "current price of", "what happened to"]
    
    needs_search = any(kw in clean_lower for kw in search_keywords)
    if (needs_search or (web_search_enabled and not urls and ("search" in clean_lower or "latest" in clean_lower or "current" in clean_lower or "news" in clean_lower))) and not urls:
        # Extract search query
        query = prompt
        for kw in search_keywords:
            if kw in clean_lower:
                idx = clean_lower.find(kw) + len(kw)
                query = prompt[idx:].strip(" ?:.,")
                break
                
        results = search_duckduckgo(query)
        if results:
            search_summary = []
            for r in results:
                sources.append(f"{r['title']} ({r['url']})")
                search_summary.append(f"- **{r['title']}**\n  {r['snippet']}\n  Source: {r['url']}")
            context_blocks.append(f"--- Live Web Search Results for: '{query}' ---\n" + "\n\n".join(search_summary))

    if not context_blocks:
        return "", []

    full_context = "\n\n```web_context\n" + "\n\n".join(context_blocks) + "\n```\n"
    return full_context, sources
