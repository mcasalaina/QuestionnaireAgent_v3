"""Column identification service using Azure AI to detect Question, Response, and Documentation columns."""

import logging
from typing import List, Dict, Optional, Tuple
import json
import re

logger = logging.getLogger(__name__)


class ColumnIdentifier:
    """Identifies Question, Response, and Documentation columns in spreadsheet headers using Azure AI."""
    
    def __init__(self, azure_client=None):
        """Initialize the column identifier.
        
        Args:
            azure_client: Optional Azure AI client for column identification.
                         If None, will use fallback heuristics.
        """
        self.azure_client = azure_client
    
    async def identify_columns(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """Identify which columns contain Questions, Responses, and Documentation.
        
        Args:
            headers: List of column header names from the spreadsheet
            
        Returns:
            Dictionary with keys 'question', 'response', 'documentation' mapping to column indices (0-based).
            Returns None for columns that cannot be identified.
            
        Example:
            headers = ['Status', 'Owner', 'Q#', 'Question', 'Response', 'Documentation']
            result = {'question': 3, 'response': 4, 'documentation': 5}
        """
        if self.azure_client:
            try:
                return await self._identify_with_ai(headers)
            except Exception as e:
                logger.warning(f"Failed to identify columns with AI, falling back to heuristics: {e}")
        
        # Fallback to heuristic-based identification
        return self._identify_with_heuristics(headers)
    
    async def _identify_with_ai(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """Use Azure AI to identify columns from headers.
        
        Args:
            headers: List of column header names
            
        Returns:
            Dictionary mapping column types to indices
        """
        # Lazy import to avoid dependency issues
        try:
            from agent_framework import ChatAgent, ChatMessage, Role
        except ImportError:
            logger.warning("agent_framework not available, falling back to heuristics")
            return self._identify_with_heuristics(headers)
        
        # Create a prompt for the AI to identify columns
        prompt = f"""You are analyzing a spreadsheet with the following column headers:
{', '.join([f'Column {i}: "{h}"' for i, h in enumerate(headers)])}

Identify which columns are:
1. Question column - contains the questions to be answered
2. Response column - where answers should be written
3. Documentation column - for documentation links (optional)

Respond ONLY with valid JSON in this exact format, no other text:
{{"question": <column_index>, "response": <column_index>, "documentation": <column_index_or_null>}}

Use 0-based column indices. If a column cannot be identified, use null.
"""
        
        logger.info(f"Sending column identification request to Azure AI with headers: {headers}")
        
        # For now, we'll use a simple approach - create a thread and message
        # This should be replaced with the actual Azure AI call pattern used in the project
        
        agent = ChatAgent(
            chat_client=self.azure_client,
            instructions="""You are a column identification expert. Analyze spreadsheet headers 
            and identify which columns contain Questions, Responses, and Documentation. 
            Always respond with valid JSON only.""",
            model="gpt-4.1-mini"
        )
        
        messages = [ChatMessage(role=Role.USER, content=prompt)]
        response = await agent.invoke(messages)
        
        # Parse the AI response
        response_text = response.messages[-1].content if response.messages else ""
        logger.info(f"Received column identification response: {response_text}")
        
        # Extract JSON from response
        result = self._parse_ai_response(response_text)
        
        # Validate the result
        if not self._validate_column_mapping(result, len(headers)):
            logger.warning("AI response validation failed, falling back to heuristics")
            return self._identify_with_heuristics(headers)
        
        logger.info(f"Successfully identified columns with AI: {result}")
        return result
    
    def _identify_with_heuristics(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """Use heuristic rules to identify columns from headers.
        
        Args:
            headers: List of column header names
            
        Returns:
            Dictionary mapping column types to indices
        """
        logger.info(f"Using heuristic identification for headers: {headers}")
        
        result = {
            'question': None,
            'response': None,
            'documentation': None
        }
        
        # Normalize headers for comparison
        normalized_headers = [h.lower().strip() if h else '' for h in headers]
        
        # Identify question column - prioritize exact/better matches
        question_keywords = [
            ('question', 10),  # Highest priority
            ('query', 8),
            ('ask', 6),
            ('prompt', 6),
            ('q', 1)  # Lowest priority - only match if standalone or at word boundary
        ]
        best_question_score = 0
        for i, header in enumerate(normalized_headers):
            for keyword, score in question_keywords:
                # For single letter 'q', be more strict
                if keyword == 'q' and (header == 'q' or header.startswith('q ')):
                    if score > best_question_score:
                        result['question'] = i
                        best_question_score = score
                elif keyword in header and len(keyword) > 1:
                    if score > best_question_score:
                        result['question'] = i
                        best_question_score = score
        
        # Identify response column
        response_keywords = ['response', 'answer', 'reply', 'result', 'output']
        for i, header in enumerate(normalized_headers):
            if any(keyword in header for keyword in response_keywords):
                result['response'] = i
                break
        
        # Identify documentation column
        doc_keywords = ['documentation', 'docs', 'reference', 'link', 'url', 'source']
        for i, header in enumerate(normalized_headers):
            if any(keyword in header for keyword in doc_keywords):
                result['documentation'] = i
                break
        
        logger.info(f"Heuristic identification result: {result}")
        return result
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Optional[int]]:
        """Parse the AI response to extract column mapping.
        
        Args:
            response_text: Raw response from AI
            
        Returns:
            Dictionary mapping column types to indices
        """
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                return result
            else:
                logger.warning("No JSON found in AI response")
                return {'question': None, 'response': None, 'documentation': None}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {'question': None, 'response': None, 'documentation': None}
    
    def _validate_column_mapping(self, mapping: Dict[str, Optional[int]], num_columns: int) -> bool:
        """Validate that the column mapping is reasonable.
        
        Args:
            mapping: Column mapping to validate
            num_columns: Total number of columns in the spreadsheet
            
        Returns:
            True if mapping is valid, False otherwise
        """
        # Must have at least question column
        if mapping.get('question') is None:
            return False
        
        # Indices must be within range
        for key, value in mapping.items():
            if value is not None:
                if not isinstance(value, int) or value < 0 or value >= num_columns:
                    return False
        
        # Question and response columns must be different
        if (mapping.get('question') is not None and 
            mapping.get('response') is not None and 
            mapping.get('question') == mapping.get('response')):
            return False
        
        return True
