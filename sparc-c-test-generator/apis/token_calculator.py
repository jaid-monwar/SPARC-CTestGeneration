"""
Token Calculator Module

Calculates and tracks token counts for each LLM API call step using tiktoken.
Saves token statistics to a file for analysis.
"""

import os
import json
import tiktoken
from datetime import datetime
from typing import Dict, List, Any, Optional
from threading import Lock


class TokenCalculator:
    """
    Singleton class to calculate and track token counts across all LLM API calls.
    Uses o200k_base encoding (for gpt-4.1 and similar models).
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, output_dir: str = "apis/tmp"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, output_dir: str = "apis/tmp"):
        if self._initialized:
            return

        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "token_calculator.json")

        # Use o200k_base encoding as specified
        self.encoding = tiktoken.get_encoding("o200k_base")

        # Token tracking by step/category
        self.token_counts: Dict[str, Dict[str, Any]] = {
            "operation_map": {"input_tokens": 0, "calls": 0, "details": []},
            "function_documentation": {"input_tokens": 0, "calls": 0, "details": []},
            "test_designer": {"input_tokens": 0, "calls": 0, "details": []},
            "test_coder": {"input_tokens": 0, "calls": 0, "details": []},
            "monolithic_test": {"input_tokens": 0, "calls": 0, "details": []},
            "validation": {"input_tokens": 0, "calls": 0, "details": []},
            "other": {"input_tokens": 0, "calls": 0, "details": []},
        }

        # Metadata
        self.start_time = datetime.now().isoformat()
        self.model = "gpt-4.1"

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        self._initialized = True
        print(f"🔢 TokenCalculator initialized with o200k_base encoding")

    def count_tokens(self, text: str) -> int:
        """
        Calculate the number of tokens in a text string.

        Args:
            text: The text to tokenize

        Returns:
            Number of tokens
        """
        if not text:
            return 0
        tokens = self.encoding.encode(text)
        return len(tokens)

    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Calculate tokens for a list of chat messages.
        Accounts for message structure overhead.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Total token count including overhead
        """
        total_tokens = 0

        for message in messages:
            # Add tokens for message content
            content = message.get("content", "")
            total_tokens += self.count_tokens(content)

            # Add overhead for message structure (role, formatting)
            # Approximately 4 tokens per message for role and delimiters
            total_tokens += 4

        # Add 3 tokens for the overall messages structure
        total_tokens += 3

        return total_tokens

    def _categorize_context(self, context: str) -> str:
        """
        Map a context string to a category.

        Args:
            context: The context string from the API call

        Returns:
            Category name
        """
        context_lower = context.lower()

        if "operation_map" in context_lower:
            return "operation_map"
        elif "function_documentation" in context_lower or "function_doc" in context_lower or "structured_doc" in context_lower:
            return "function_documentation"
        elif "test_designer" in context_lower:
            return "test_designer"
        elif "test_coder" in context_lower:
            return "test_coder"
        elif "monolithic_test" in context_lower:
            return "monolithic_test"
        elif "validation" in context_lower or "c_code_validation" in context_lower:
            return "validation"
        else:
            return "other"

    def track_tokens(
        self,
        messages: List[Dict[str, str]],
        context: str,
        model: str = "gpt-4.1"
    ) -> int:
        """
        Track tokens for an API call.

        Args:
            messages: List of message dicts
            context: Context string identifying the call type
            model: Model name (for logging)

        Returns:
            Token count for this call
        """
        token_count = self.count_message_tokens(messages)
        category = self._categorize_context(context)

        with self._lock:
            self.token_counts[category]["input_tokens"] += token_count
            self.token_counts[category]["calls"] += 1
            self.token_counts[category]["details"].append({
                "context": context,
                "tokens": token_count,
                "timestamp": datetime.now().isoformat(),
            })
            self.model = model

        return token_count

    def get_total_tokens(self) -> int:
        """Get the total input tokens across all categories."""
        return sum(cat["input_tokens"] for cat in self.token_counts.values())

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of token usage.

        Returns:
            Dictionary with token usage summary
        """
        total_tokens = self.get_total_tokens()
        total_calls = sum(cat["calls"] for cat in self.token_counts.values())

        summary = {
            "metadata": {
                "start_time": self.start_time,
                "end_time": datetime.now().isoformat(),
                "model": self.model,
                "encoding": "o200k_base",
            },
            "totals": {
                "total_input_tokens": total_tokens,
                "total_api_calls": total_calls,
            },
            "by_step": {},
        }

        for step, data in self.token_counts.items():
            if data["calls"] > 0:
                summary["by_step"][step] = {
                    "input_tokens": data["input_tokens"],
                    "api_calls": data["calls"],
                    "avg_tokens_per_call": round(data["input_tokens"] / data["calls"], 2) if data["calls"] > 0 else 0,
                }

        return summary

    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Get a detailed report including all individual calls.

        Returns:
            Dictionary with detailed token usage
        """
        report = self.get_summary()
        report["details"] = {}

        for step, data in self.token_counts.items():
            if data["calls"] > 0:
                report["details"][step] = data["details"]

        return report

    def save(self, detailed: bool = False) -> str:
        """
        Save token counts to file.

        Args:
            detailed: If True, include individual call details

        Returns:
            Path to the saved file
        """
        if detailed:
            data = self.get_detailed_report()
        else:
            data = self.get_summary()

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"💾 Token counts saved to: {self.output_file}")
        return self.output_file

    def print_summary(self):
        """Print a formatted summary of token usage."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("📊 TOKEN USAGE SUMMARY")
        print("=" * 60)
        print(f"Model: {summary['metadata']['model']}")
        print(f"Encoding: {summary['metadata']['encoding']}")
        print("-" * 60)

        print(f"\n{'Step':<25} {'Tokens':>12} {'API Calls':>12} {'Avg/Call':>12}")
        print("-" * 60)

        for step, data in summary["by_step"].items():
            print(f"{step:<25} {data['input_tokens']:>12,} {data['api_calls']:>12} {data['avg_tokens_per_call']:>12,.2f}")

        print("-" * 60)
        print(f"{'TOTAL':<25} {summary['totals']['total_input_tokens']:>12,} {summary['totals']['total_api_calls']:>12}")
        print("=" * 60 + "\n")

    def reset(self):
        """Reset all token counts."""
        with self._lock:
            for category in self.token_counts:
                self.token_counts[category] = {"input_tokens": 0, "calls": 0, "details": []}
            self.start_time = datetime.now().isoformat()
        print("🔄 TokenCalculator reset")

    def set_output_dir(self, output_dir: str):
        """
        Set the output directory for saving token counts.

        Args:
            output_dir: Directory to save token_calculator.json
        """
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "token_calculator.json")
        os.makedirs(output_dir, exist_ok=True)


# Global instance accessor
_token_calculator: Optional[TokenCalculator] = None


def get_token_calculator(output_dir: str = "apis/tmp") -> TokenCalculator:
    """
    Get or create the global TokenCalculator instance.

    Args:
        output_dir: Directory to save token counts

    Returns:
        TokenCalculator instance
    """
    global _token_calculator
    if _token_calculator is None:
        _token_calculator = TokenCalculator(output_dir)
    return _token_calculator


def reset_token_calculator():
    """Reset the global token calculator."""
    global _token_calculator
    if _token_calculator:
        _token_calculator.reset()
