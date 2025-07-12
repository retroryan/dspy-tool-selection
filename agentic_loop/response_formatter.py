"""
Response formatting module for the agentic loop implementation.

This module provides DSPy-based response formatting with different output styles
and formats conversation history for human and LLM consumption.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
import dspy
from shared.models import ConversationEntry, ToolExecutionResult, ToolCall


class ResponseStyle(str, Enum):
    """Different response formatting styles."""
    DETAILED = "detailed"
    CONCISE = "concise"
    SUMMARY = "summary"
    TECHNICAL = "technical"


class ResponseFormatterSignature(dspy.Signature):
    """Signature for formatting agent responses."""
    
    raw_response: str = dspy.InputField(
        desc="The raw response from the agent reasoning"
    )
    tool_results: str = dspy.InputField(
        desc="JSON formatted results from tool executions"
    )
    conversation_context: str = dspy.InputField(
        desc="Relevant context from previous conversation"
    )
    response_style: str = dspy.InputField(
        desc="Desired response style (detailed, concise, summary, technical)"
    )
    confidence_score: float = dspy.InputField(
        desc="Confidence score from agent reasoning (0-1)"
    )
    
    formatted_response: str = dspy.OutputField(
        desc="Final formatted response incorporating all elements"
    )
    confidence_statement: str = dspy.OutputField(
        desc="Human-readable confidence statement"
    )
    key_points: List[str] = dspy.OutputField(
        desc="Key points extracted from the response"
    )


class ConversationSummarySignature(dspy.Signature):
    """Signature for summarizing conversation history."""
    
    conversation_entries: str = dspy.InputField(
        desc="JSON formatted conversation history entries"
    )
    focus_query: str = dspy.InputField(
        desc="Current user query to focus the summary"
    )
    
    summary: str = dspy.OutputField(
        desc="Concise summary of conversation history"
    )
    key_insights: List[str] = dspy.OutputField(
        desc="Key insights and decisions from the conversation"
    )
    relevant_context: str = dspy.OutputField(
        desc="Most relevant context for current query"
    )


class ResponseFormatter(dspy.Module):
    """DSPy module for formatting agent responses with different styles."""
    
    def __init__(self, default_style: ResponseStyle = ResponseStyle.DETAILED):
        """
        Initialize the ResponseFormatter.
        
        Args:
            default_style: Default response formatting style
        """
        super().__init__()
        self.default_style = default_style
        
        # Main response formatter
        self.formatter = dspy.ChainOfThought(ResponseFormatterSignature)
        
        # Conversation summarizer
        self.summarizer = dspy.ChainOfThought(ConversationSummarySignature)
        
        # Confidence interpreter
        self.confidence_interpreter = dspy.Predict(
            "confidence_score -> confidence_level:str, explanation:str"
        )
    
    def forward(self, raw_response: str, tool_results: List[ToolExecutionResult], 
                conversation_context: str = "", response_style: Optional[ResponseStyle] = None,
                confidence_score: float = 0.5) -> dspy.Prediction:
        """
        Format the agent response with specified style.
        
        Args:
            raw_response: Raw response from agent reasoning
            tool_results: Results from tool executions
            conversation_context: Previous conversation context
            response_style: Desired response style
            confidence_score: Confidence from agent reasoning
            
        Returns:
            DSPy prediction with formatted response
        """
        # Use provided style or default
        style = response_style or self.default_style
        
        # Format tool results for LLM consumption
        formatted_tool_results = self._format_tool_results(tool_results)
        
        # Format the response
        result = self.formatter(
            raw_response=raw_response,
            tool_results=formatted_tool_results,
            conversation_context=conversation_context,
            response_style=style.value,
            confidence_score=confidence_score
        )
        
        return result
    
    def format_conversation_summary(self, conversation_entries: List[ConversationEntry], 
                                  focus_query: str) -> dspy.Prediction:
        """
        Create a summary of conversation history.
        
        Args:
            conversation_entries: List of conversation entries
            focus_query: Current query to focus the summary
            
        Returns:
            DSPy prediction with conversation summary
        """
        # Format conversation entries for LLM consumption
        formatted_entries = self._format_conversation_entries(conversation_entries)
        
        # Generate summary
        result = self.summarizer(
            conversation_entries=formatted_entries,
            focus_query=focus_query
        )
        
        return result
    
    def interpret_confidence(self, confidence_score: float) -> Dict[str, str]:
        """
        Interpret confidence score into human-readable format.
        
        Args:
            confidence_score: Confidence score (0-1)
            
        Returns:
            Dictionary with confidence level and explanation
        """
        try:
            result = self.confidence_interpreter(confidence_score=confidence_score)
            return {
                "level": result.confidence_level,
                "explanation": result.explanation
            }
        except Exception as e:
            # Fallback to simple interpretation
            if confidence_score >= 0.8:
                return {"level": "High", "explanation": "Very confident in the response"}
            elif confidence_score >= 0.6:
                return {"level": "Medium", "explanation": "Moderately confident in the response"}
            else:
                return {"level": "Low", "explanation": "Low confidence, may need more information"}
    
    def _format_tool_results(self, tool_results: List[ToolExecutionResult]) -> str:
        """Format tool results for LLM consumption."""
        if not tool_results:
            return "No tool results available"
        
        formatted_results = []
        for result in tool_results:
            status = "✅ Success" if result.success else "❌ Failed"
            formatted_results.append(
                f"Tool: {result.tool_name}\n"
                f"Status: {status}\n"
                f"Result: {result.result}\n"
                f"Error: {result.error or 'None'}\n"
            )
        
        return "\n".join(formatted_results)
    
    def _format_conversation_entries(self, entries: List[ConversationEntry]) -> str:
        """Format conversation entries for LLM consumption."""
        if not entries:
            return "No conversation history available"
        
        formatted_entries = []
        for entry in entries:
            tools_used = [call.tool_name for call in entry.tool_calls_made]
            tools_str = f"Tools used: {', '.join(tools_used)}" if tools_used else "No tools used"
            
            formatted_entries.append(
                f"Iteration {entry.iteration}:\n"
                f"User: {entry.user_input}\n"
                f"Agent: {entry.response}\n"
                f"{tools_str}\n"
            )
        
        return "\n".join(formatted_entries)


class ConversationManager(dspy.Module):
    """Manages conversation history and provides formatting utilities."""
    
    def __init__(self, max_history_length: int = 10, 
                 auto_summarize_threshold: int = 20):
        """
        Initialize the ConversationManager.
        
        Args:
            max_history_length: Maximum entries to keep in detailed history
            auto_summarize_threshold: Threshold for automatic summarization
        """
        super().__init__()
        self.max_history_length = max_history_length
        self.auto_summarize_threshold = auto_summarize_threshold
        
        # Response formatter for conversation formatting
        self.response_formatter = ResponseFormatter()
        
        # History compression
        self.history_compressor = dspy.ChainOfThought(
            "long_history -> compressed_history:str, preserved_context:str"
        )
    
    def add_conversation_entry(self, entries: List[ConversationEntry], 
                             new_entry: ConversationEntry) -> List[ConversationEntry]:
        """
        Add a new conversation entry and manage history length.
        
        Args:
            entries: Current conversation entries
            new_entry: New entry to add
            
        Returns:
            Updated conversation entries list
        """
        # Add new entry
        updated_entries = entries + [new_entry]
        
        # Check if we need to compress history
        if len(updated_entries) > self.auto_summarize_threshold:
            updated_entries = self._compress_history(updated_entries)
        elif len(updated_entries) > self.max_history_length:
            # Simple truncation if not hitting auto-summarize threshold
            updated_entries = updated_entries[-self.max_history_length:]
        
        return updated_entries
    
    def format_history_for_llm(self, entries: List[ConversationEntry]) -> str:
        """
        Format conversation history for LLM consumption.
        
        Args:
            entries: Conversation entries to format
            
        Returns:
            Formatted history string
        """
        return self.response_formatter._format_conversation_entries(entries)
    
    def format_history_for_human(self, entries: List[ConversationEntry]) -> str:
        """
        Format conversation history for human reading.
        
        Args:
            entries: Conversation entries to format
            
        Returns:
            Human-readable formatted history
        """
        if not entries:
            return "No conversation history available."
        
        formatted_entries = []
        for entry in entries:
            # Format timestamp
            import datetime
            timestamp = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
            
            # Format tools and results
            tools_section = ""
            if entry.tool_calls_made:
                tools_section = f"\n  📱 Tools used: {', '.join(call.tool_name for call in entry.tool_calls_made)}"
                
                # Add tool results if available
                if entry.tool_results:
                    successful_tools = [r.tool_name for r in entry.tool_results if r.success]
                    failed_tools = [r.tool_name for r in entry.tool_results if not r.success]
                    
                    if successful_tools:
                        tools_section += f"\n  ✅ Successful: {', '.join(successful_tools)}"
                    if failed_tools:
                        tools_section += f"\n  ❌ Failed: {', '.join(failed_tools)}"
            
            formatted_entries.append(
                f"[{timestamp}] Iteration {entry.iteration}:\n"
                f"  👤 User: {entry.user_input}\n"
                f"  🤖 Agent: {entry.response}"
                f"{tools_section}\n"
            )
        
        return "\n".join(formatted_entries)
    
    def _compress_history(self, entries: List[ConversationEntry]) -> List[ConversationEntry]:
        """
        Compress conversation history when it gets too long.
        
        Args:
            entries: Current conversation entries
            
        Returns:
            Compressed conversation entries
        """
        if len(entries) <= self.max_history_length:
            return entries
        
        # Keep recent entries and compress older ones
        recent_entries = entries[-self.max_history_length:]
        older_entries = entries[:-self.max_history_length]
        
        # Format older entries for compression
        older_formatted = self.response_formatter._format_conversation_entries(older_entries)
        
        try:
            # Compress older history
            compression_result = self.history_compressor(long_history=older_formatted)
            
            # Create a summary entry
            summary_entry = ConversationEntry(
                iteration=0,  # Special iteration for summary
                user_input="[COMPRESSED HISTORY]",
                response=f"Summary: {compression_result.compressed_history}\nContext: {compression_result.preserved_context}",
                tool_calls_made=[],
                tool_results=[]
            )
            
            return [summary_entry] + recent_entries
        except Exception as e:
            # Fallback to simple truncation
            return recent_entries
    
    def get_conversation_stats(self, entries: List[ConversationEntry]) -> Dict[str, Any]:
        """
        Get statistics about the conversation.
        
        Args:
            entries: Conversation entries to analyze
            
        Returns:
            Dictionary with conversation statistics
        """
        if not entries:
            return {
                "total_iterations": 0,
                "total_tools_used": 0,
                "success_rate": 0.0,
                "most_used_tools": [],
                "average_response_length": 0
            }
        
        # Calculate statistics
        total_iterations = len(entries)
        total_tools_used = sum(len(entry.tool_calls_made) for entry in entries)
        
        # Success rate calculation
        total_tool_executions = sum(len(entry.tool_results) for entry in entries)
        successful_executions = sum(
            sum(1 for result in entry.tool_results if result.success) 
            for entry in entries
        )
        success_rate = successful_executions / total_tool_executions if total_tool_executions > 0 else 0.0
        
        # Most used tools
        tool_usage = {}
        for entry in entries:
            for tool_call in entry.tool_calls_made:
                tool_usage[tool_call.tool_name] = tool_usage.get(tool_call.tool_name, 0) + 1
        
        most_used_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Average response length
        response_lengths = [len(entry.response) for entry in entries]
        average_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
        
        return {
            "total_iterations": total_iterations,
            "total_tools_used": total_tools_used,
            "success_rate": success_rate,
            "most_used_tools": most_used_tools,
            "average_response_length": average_response_length
        }