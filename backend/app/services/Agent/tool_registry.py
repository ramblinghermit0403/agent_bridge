
import logging
from typing import List, Dict, Any, Union
from langchain_core.tools import StructuredTool
from rank_bm25 import BM25Okapi
import re

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Registry for managing and searching tools using BM25 and keyword matching.
    """
    def __init__(self):
        self._tools: Dict[str, StructuredTool] = {}
        self._bm25 = None
        self._corpus = []
        self._tool_names = []

    def register_tools(self, tools: List[StructuredTool]):
        """
        Registers a list of tools and rebuilds the search index.
        """
        for tool in tools:
            self._tools[tool.name] = tool
        
        self._rebuild_index()

    def _rebuild_index(self):
        """
        Rebuilds the BM25 index based on current tools.
        """
        self._tool_names = list(self._tools.keys())
        # Create corpus from tool name and description
        self._corpus = [
            self._tokenize(f"{name} {self._tools[name].description}") 
            for name in self._tool_names
        ]
        if self._corpus:
            self._bm25 = BM25Okapi(self._corpus)
        else:
            self._bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenizer that splits by non-alphanumeric characters and lowercases.
        """
        return re.split(r'\W+', text.lower())

    def search(self, query: str, limit: int = 5, mode: str = "bm25") -> List[StructuredTool]:
        """
        Search for tools matching the query.
        
        Args:
            query: The search query.
            limit: Maximum number of tools to return.
            mode: "bm25" (semantic-ish) or "keyword" (substring match).
        """
        if not self._tools:
            return []

        if mode == "keyword":
            results = []
            query_lower = query.lower()
            for name, tool in self._tools.items():
                if query_lower in name.lower() or query_lower in tool.description.lower():
                    results.append(tool)
                if len(results) >= limit:
                    break
            return results
        
        elif mode == "bm25":
            if not self._bm25:
                # Fallback to keyword if index build failed or empty
                return self.search(query, limit, mode="keyword")
            
            tokenized_query = self._tokenize(query)
            scores = self._bm25.get_scores(tokenized_query)
            
            # Zip scores with tool names and sort
            scored_tools = sorted(
                zip(self._tool_names, scores), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # content filtering: return tools with score > 0
            top_tools = [
                self._tools[name] 
                for name, score in scored_tools 
                if score > 0
            ][:limit]
            
            return top_tools
        
        else:
            logger.warning(f"Unknown search mode '{mode}', defaulting to keyword.")
            return self.search(query, limit, mode="keyword")

    def get_tool(self, tool_name: str) -> Union[StructuredTool, None]:
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[StructuredTool]:
        return list(self._tools.values())
