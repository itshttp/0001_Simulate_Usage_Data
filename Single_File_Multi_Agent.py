"""
Single-File Web Research System
Core functionality: Web Search, Analyze Results, and Respond to Questions

Requirements:
    pip install streamlit openai ddgs requests beautifulsoup4
    (or use: pip install duckduckgo-search as fallback)
    Set OPENAI_API_KEY environment variable or in .env file
"""

import streamlit as st
import os
import warnings
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

# Suppress deprecation warnings (especially for duckduckgo_search package rename)
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*has been renamed.*")

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import web search library (suppress deprecation warning)
DDGS = None
DDGS_AVAILABLE = False
try:
    # Suppress RuntimeWarning about package rename
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            from ddgs import DDGS  # Try new package name first
            DDGS_AVAILABLE = True
        except ImportError:
            from duckduckgo_search import DDGS  # Fallback to old package name
            DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Try to import website scraping libraries
REQUESTS_AVAILABLE = False
BEAUTIFULSOUP_AVAILABLE = False
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


# ============================================
# WEB RESEARCH AGENT
# ============================================
class WebResearchAgent:
    """Core agent for web research: search, analyze, and respond."""

    def __init__(self, llm_model: str = "gpt-4o-mini", llm_provider: str = "openai"):
        """
        Initialize web research agent.

        Args:
            llm_model: LLM model name to use
            llm_provider: LLM provider ("openai", "mock")
        """
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.client = None
        self.api_key = None
        
        if llm_provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key:
                self.api_key = api_key
                self.client = OpenAI(api_key=api_key)
            else:
                self.llm_provider = "mock"

    def search_and_analyze(self, question: str, num_results: int = 5) -> Dict:
        """
        Core function: Search web, analyze results, and respond to question.

        Args:
            question: Research question to investigate
            num_results: Number of search results to analyze (default: 5)

        Returns:
            Dictionary with status, search results, and summary
        """
        try:
            if not question or not question.strip():
                return {
                    "status": "error",
                    "error": "No research question provided"
                }

            # Step 1: Search the web
            search_results = self._search_web(question, num_results)
            
            if not search_results:
                return {
                    "status": "error",
                    "error": "No search results found. Please check your internet connection or try a different query."
                }

            # Step 2: Analyze results and generate summary
            summary = self._analyze_results(search_results, question)

            # Step 3: Return response
            return {
                "status": "success",
                "question": question,
                "search_results": search_results,
                "summary": summary,
                "num_results": len(search_results)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search the web and return top results."""
        results = []
        
        # Use DuckDuckGo Search
        if DDGS_AVAILABLE:
            try:
                # Suppress deprecation warning during search
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=RuntimeWarning)
                    with DDGS() as ddgs:
                        search_results = list(ddgs.text(query, max_results=num_results))
                        for result in search_results[:num_results]:
                            results.append({
                                'title': result.get('title', 'No title'),
                                'url': result.get('href', ''),
                                'snippet': result.get('body', 'No description')
                            })
                        if results:
                            return results
            except Exception as e:
                st.warning(f"Search failed: {str(e)}")
        
        # Fallback: Mock results
        if not results:
            st.warning("⚠️ Web search library not available. Install with: pip install ddgs (or duckduckgo-search)")
            return self._mock_search_results(query, num_results)
        
        return results

    def _analyze_results(self, search_results: List[Dict[str, str]], question: str) -> str:
        """Analyze search results and generate summary using LLM."""
        # Format results for LLM
        formatted_content = f"Research Question: {question}\n\n"
        formatted_content += "Web Search Results:\n"
        formatted_content += "=" * 50 + "\n\n"
        
        for i, result in enumerate(search_results, 1):
            formatted_content += f"Result {i}:\n"
            formatted_content += f"Title: {result.get('title', 'N/A')}\n"
            formatted_content += f"URL: {result.get('url', 'N/A')}\n"
            formatted_content += f"Content: {result.get('snippet', 'No description')}\n"
            formatted_content += "-" * 50 + "\n\n"
        
        formatted_content += "\nPlease summarize the key information to answer the research question."
        
        # Generate summary using LLM
        system_prompt = """You are a research analyst. Analyze the web search results and provide a comprehensive summary to answer the user's question.

Your tasks:
1. Analyze all search results from multiple sources
2. Extract key information relevant to the question
3. Provide a clear, comprehensive summary
4. Cite sources when possible
5. Highlight any conflicting information

Output format:
## Summary
(Concise summary of findings)

## Key Points
1. [Key point from sources]
2. [Key point from sources]
3. [Key point from sources]

## Sources
(List of sources referenced)"""

        return self._call_llm(system_prompt, formatted_content)

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call LLM to generate response."""
        try:
            if self.llm_provider == "openai" and self.client:
                api_key = os.getenv("OPENAI_API_KEY", self.api_key or "")
                if api_key and OPENAI_AVAILABLE:
                    if not self.client or self.api_key != api_key:
                        self.api_key = api_key
                        self.client = OpenAI(api_key=api_key)
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                    
                    response = self.client.chat.completions.create(
                        model=self.llm_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    return response.choices[0].message.content.strip()
            
            # Mock response for testing
            return self._mock_summary(user_message)
        except Exception as e:
            return f"LLM call failed: {str(e)}"

    def _mock_search_results(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Generate mock search results for testing."""
        return [
            {
                'title': f'Mock Result {i} for: {query}',
                'url': f'https://example.com/result{i}',
                'snippet': f'This is a mock search result {i}. Install duckduckgo-search for real results.'
            }
            for i in range(1, num_results + 1)
        ]

    def _mock_summary(self, content: str) -> str:
        """Generate mock summary for testing."""
        return """## Summary
Mock summary: This is a placeholder response. Please set OPENAI_API_KEY environment variable for real AI-generated summaries.

## Key Points
1. Install duckduckgo-search for web search
2. Set OPENAI_API_KEY for AI summaries
3. Review the search results tab for source information

## Sources
- See search results tab for actual sources"""


# ============================================
# WEBSITE SEARCH AGENT
# ============================================
class WebsiteSearchAgent:
    """Agent that understands questions, identifies websites, and searches them directly."""

    def __init__(self, llm_model: str = "gpt-4o-mini", llm_provider: str = "openai"):
        """
        Initialize website search agent.

        Args:
            llm_model: LLM model name to use
            llm_provider: LLM provider ("openai", "mock")
        """
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.client = None
        self.api_key = None
        
        if llm_provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key:
                self.api_key = api_key
                self.client = OpenAI(api_key=api_key)
            else:
                self.llm_provider = "mock"

    def search_websites(self, question: str, max_websites: int = 3) -> Dict:
        """
        Core function: Understand question, identify websites, search them directly, and return results.

        Args:
            question: Research question to investigate
            max_websites: Maximum number of websites to search (default: 3)

        Returns:
            Dictionary with status, websites searched, content extracted, and summary
        """
        try:
            if not question or not question.strip():
                return {
                    "status": "error",
                    "error": "No research question provided"
                }

            # Step 1: Understand question and identify websites to search
            websites_to_search = self._identify_websites(question, max_websites)
            
            if not websites_to_search:
                return {
                    "status": "error",
                    "error": "Could not identify relevant websites to search. Please try a more specific question."
                }

            # Step 2: Visit websites and extract content
            website_results = []
            for website_url in websites_to_search:
                content = self._extract_website_content(website_url, question)
                if content:
                    website_results.append({
                        'url': website_url,
                        'title': content.get('title', website_url),
                        'content': content.get('content', ''),
                        'excerpt': content.get('excerpt', '')
                    })

            if not website_results:
                return {
                    "status": "error",
                    "error": "Could not extract content from identified websites. They may require authentication or have blocking mechanisms."
                }

            # Step 3: Analyze extracted content and generate summary
            summary = self._analyze_website_content(website_results, question)

            # Step 4: Return response
            return {
                "status": "success",
                "question": question,
                "websites_searched": websites_to_search,
                "website_results": website_results,
                "summary": summary,
                "num_results": len(website_results)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _identify_websites(self, question: str, max_websites: int = 3) -> List[str]:
        """Use LLM to understand question and identify relevant websites to search."""
        system_prompt = """You are a web research assistant. Given a user's question, identify the most relevant websites that would contain information to answer it.

Your task:
1. Analyze the question to understand what information is needed
2. Identify 1-3 specific websites that are likely to have relevant information
3. Provide the full URLs (https://...) of these websites
4. Focus on authoritative sources (official sites, news sites, documentation, etc.)

Output format (one URL per line, no explanations):
https://example.com/page1
https://example.com/page2
https://example.com/page3

If you cannot identify specific URLs, provide domain names and the agent will search for relevant pages."""

        try:
            if self.llm_provider == "openai" and self.client:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question}\n\nIdentify {max_websites} relevant websites to search:"}
                ]
                
                response = self.client.chat.completions.create(
                    model=self.llm_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500
                )
                
                llm_output = response.choices[0].message.content.strip()
                # Extract URLs from LLM response
                urls = self._extract_urls_from_text(llm_output)
                return urls[:max_websites]
            
            # Mock response for testing
            return self._mock_identify_websites(question, max_websites)
        except Exception as e:
            st.warning(f"Failed to identify websites: {str(e)}")
            return []

    def _extract_urls_from_text(self, text: str) -> List[str]:
        """Extract URLs from text using regex."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            url = url.rstrip('.,;:!?')
            if url:
                cleaned_urls.append(url)
        return cleaned_urls

    def _extract_website_content(self, url: str, question: str) -> Optional[Dict[str, str]]:
        """Visit website directly and extract relevant content."""
        if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
            return None

        try:
            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make request with timeout
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url
            
            # Extract main content
            # Try to find main content areas
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '#content', 'body']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Get text content
                content_text = main_content.get_text(separator='\n', strip=True)
                # Clean up whitespace
                content_lines = [line.strip() for line in content_text.split('\n') if line.strip()]
                content_text = '\n'.join(content_lines)
                
                # Create excerpt (first 500 chars)
                excerpt = content_text[:500] + '...' if len(content_text) > 500 else content_text
                
                return {
                    'title': title_text,
                    'content': content_text,
                    'excerpt': excerpt,
                    'url': url
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            st.warning(f"Failed to fetch {url}: {str(e)}")
            return None
        except Exception as e:
            st.warning(f"Error processing {url}: {str(e)}")
            return None

    def _analyze_website_content(self, website_results: List[Dict[str, str]], question: str) -> str:
        """Analyze extracted website content and generate summary using LLM."""
        # Format results for LLM
        formatted_content = f"Research Question: {question}\n\n"
        formatted_content += "Content Extracted from Websites:\n"
        formatted_content += "=" * 50 + "\n\n"
        
        for i, result in enumerate(website_results, 1):
            formatted_content += f"Website {i}:\n"
            formatted_content += f"URL: {result.get('url', 'N/A')}\n"
            formatted_content += f"Title: {result.get('title', 'N/A')}\n"
            formatted_content += f"Content:\n{result.get('content', 'No content extracted')}\n"
            formatted_content += "-" * 50 + "\n\n"
        
        formatted_content += "\nPlease analyze the content from these websites and provide a comprehensive summary to answer the research question."
        
        # Generate summary using LLM
        system_prompt = """You are a research analyst. Analyze the content extracted from websites and provide a comprehensive summary to answer the user's question.

Your tasks:
1. Analyze all content from multiple websites
2. Extract key information relevant to the question
3. Provide a clear, comprehensive summary
4. Cite sources when possible
5. Highlight any conflicting information

Output format:
## Summary
(Concise summary of findings)

## Key Points
1. [Key point from sources]
2. [Key point from sources]
3. [Key point from sources]

## Sources
(List of websites referenced)"""

        return self._call_llm(system_prompt, formatted_content)

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call LLM to generate response."""
        try:
            if self.llm_provider == "openai" and self.client:
                api_key = os.getenv("OPENAI_API_KEY", self.api_key or "")
                if api_key and OPENAI_AVAILABLE:
                    if not self.client or self.api_key != api_key:
                        self.api_key = api_key
                        self.client = OpenAI(api_key=api_key)
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                    
                    response = self.client.chat.completions.create(
                        model=self.llm_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    return response.choices[0].message.content.strip()
            
            # Mock response for testing
            return self._mock_summary(user_message)
        except Exception as e:
            return f"LLM call failed: {str(e)}"

    def _mock_identify_websites(self, question: str, max_websites: int = 3) -> List[str]:
        """Generate mock website URLs for testing."""
        # Try to infer website from question
        question_lower = question.lower()
        websites = []
        
        if 'python' in question_lower:
            websites.append('https://docs.python.org/3/')
        elif 'javascript' in question_lower or 'js' in question_lower:
            websites.append('https://developer.mozilla.org/en-US/docs/Web/JavaScript')
        elif 'ai' in question_lower or 'machine learning' in question_lower:
            websites.append('https://openai.com/research')
            websites.append('https://www.deeplearning.ai')
        else:
            websites.append('https://en.wikipedia.org/wiki/Main_Page')
            websites.append('https://www.reddit.com')
        
        return websites[:max_websites]

    def _mock_summary(self, content: str) -> str:
        """Generate mock summary for testing."""
        return """## Summary
Mock summary: This is a placeholder response. Please set OPENAI_API_KEY environment variable for real AI-generated summaries.

## Key Points
1. Install requests and beautifulsoup4 for website scraping
2. Set OPENAI_API_KEY for AI summaries
3. Review the website results tab for source information

## Sources
- See website results tab for actual sources"""


# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.set_page_config(
        page_title="Web Research System",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Web Research System")
    st.markdown("*Search the web, analyze results, and get AI-powered summaries*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # LLM Configuration
        st.subheader("🤖 LLM Settings")
        
        if not OPENAI_AVAILABLE:
            st.warning("⚠️ OpenAI package not installed. Install with: pip install openai")
        
        current_api_key = os.getenv("OPENAI_API_KEY", "")
        
        if not current_api_key:
            st.warning("⚠️ OPENAI_API_KEY not set. Using mock responses.")
            st.info("💡 Set OPENAI_API_KEY environment variable or create .env file")
            llm_provider = "mock"
        else:
            llm_provider = "openai"
        
        llm_model = st.selectbox(
            "LLM Model",
            options=[
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ],
            index=0,
            help="Choose which LLM model to use"
        )
        
        # Option to manually set API key
        manual_api_key = st.text_input(
            "OpenAI API Key (optional)",
            type="password",
            help="Leave empty to use OPENAI_API_KEY environment variable"
        )
        
        if manual_api_key:
            os.environ["OPENAI_API_KEY"] = manual_api_key
            current_api_key = manual_api_key
            llm_provider = "openai"

        # Web Search Status
        st.divider()
        st.subheader("🔍 Search Status")
        if DDGS_AVAILABLE:
            st.success("✅ Web search (Google/DuckDuckGo) available")
        else:
            st.warning("⚠️ Install: pip install ddgs")
        
        if REQUESTS_AVAILABLE and BEAUTIFULSOUP_AVAILABLE:
            st.success("✅ Website scraping available")
        else:
            st.warning("⚠️ Install: pip install requests beautifulsoup4")
    
    # Main interface
    st.header("🌐 Ask Your Research Question")
    
    # Search method selection
    search_method = st.radio(
        "Choose Search Method:",
        options=["🔍 Web Search (Google/DuckDuckGo)", "🌐 Direct Website Search"],
        help="Web Search: Uses search engines. Direct Website Search: Identifies and visits specific websites directly.",
        horizontal=True
    )
    
    research_question = st.text_input(
        "Enter your question",
        placeholder="e.g., What are the latest trends in AI in 2024?" if search_method == "🔍 Web Search (Google/DuckDuckGo)" else "e.g., How does Python handle async programming?",
        help="Enter your research question and click 'Research' to search and get a summary",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        research_button = st.button("🔍 Research", type="primary", use_container_width=True)
    
    # Handle research
    if research_button:
        if not research_question or not research_question.strip():
            st.error("❌ Please enter a research question")
        else:
            # Determine LLM provider
            manual_key = manual_api_key if 'manual_api_key' in locals() and manual_api_key else ""
            final_api_key = manual_key if manual_key else os.getenv("OPENAI_API_KEY", "")
            research_llm_provider = "openai" if final_api_key else "mock"
            
            # Choose agent based on search method
            use_website_search = search_method == "🌐 Direct Website Search"
            
            if use_website_search:
                # Use WebsiteSearchAgent - understands question and searches websites directly
                if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
                    st.error("❌ Website scraping libraries not available. Install with: pip install requests beautifulsoup4")
                else:
                    website_agent = WebsiteSearchAgent(
                        llm_model=llm_model,
                        llm_provider=research_llm_provider
                    )
                    
                    # Execute research: Identify websites -> Extract content -> Analyze
                    with st.spinner("🤔 Understanding question and identifying websites to search..."):
                        result = website_agent.search_websites(research_question, max_websites=3)
                    
                    if result.get('status') == 'success':
                        st.success("✅ Research completed!")
                        
                        # Display results in tabs
                        tab1, tab2 = st.tabs(["📝 Summary", "🌐 Website Results"])
                        
                        with tab1:
                            st.subheader(f"Summary for: {result['question']}")
                            st.markdown(result['summary'])
                            st.metric("Websites Searched", result['num_results'])
                        
                        with tab2:
                            st.subheader(f"Content from {result['num_results']} Websites")
                            for i, website_result in enumerate(result['website_results'], 1):
                                with st.expander(f"{i}. {website_result.get('title', 'No title')}"):
                                    st.write(f"**URL:** [{website_result.get('url', 'N/A')}]({website_result.get('url', '#')})")
                                    st.write(f"**Excerpt:** {website_result.get('excerpt', 'No excerpt available')}")
                                    if st.checkbox(f"Show full content", key=f"show_full_{i}"):
                                        st.text_area(
                                            "Full Content",
                                            value=website_result.get('content', 'No content'),
                                            height=300,
                                            key=f"content_{i}",
                                            disabled=True
                                        )
                    else:
                        st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")
            else:
                # Use WebResearchAgent - searches via Google/DuckDuckGo
                research_agent = WebResearchAgent(
                    llm_model=llm_model,
                    llm_provider=research_llm_provider
                )
                
                # Execute research: Search -> Analyze -> Respond
                with st.spinner("🔍 Searching the web and generating summary..."):
                    result = research_agent.search_and_analyze(research_question, num_results=5)
                
                if result.get('status') == 'success':
                    st.success("✅ Research completed!")
                    
                    # Display results in tabs
                    tab1, tab2 = st.tabs(["📝 Summary", "🔗 Search Results"])
                    
                    with tab1:
                        st.subheader(f"Summary for: {result['question']}")
                        st.markdown(result['summary'])
                        st.metric("Sources Analyzed", result['num_results'])
                    
                    with tab2:
                        st.subheader(f"Top {result['num_results']} Search Results")
                        for i, search_result in enumerate(result['search_results'], 1):
                            with st.expander(f"{i}. {search_result.get('title', 'No title')}"):
                                st.write(f"**URL:** [{search_result.get('url', 'N/A')}]({search_result.get('url', '#')})")
                                st.write(f"**Snippet:** {search_result.get('snippet', 'No description')}")
                else:
                    st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")


# ============================================
# RUN APPLICATION
# ============================================
if __name__ == "__main__":
    main()
