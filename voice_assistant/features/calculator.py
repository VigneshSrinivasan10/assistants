"""
Calculator feature for voice assistant.
Handles basic arithmetic and mathematical operations.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Calculator:
    """Simple calculator for voice queries."""

    def __init__(self):
        """Initialize calculator."""
        pass

    def _is_math_query(self, query: str) -> bool:
        """
        Check if query is a math calculation.
        
        Args:
            query: User's query
            
        Returns:
            True if query contains math operations
        """
        query_lower = query.lower()
        
        # Math keywords
        math_keywords = [
            'calculate', 'compute', 'what is', 'what\'s',
            'plus', 'minus', 'times', 'divided by', 'multiply',
            'add', 'subtract', 'divide'
        ]
        
        # Check for math keywords or numbers with operators
        has_keyword = any(keyword in query_lower for keyword in math_keywords)
        has_numbers_and_ops = bool(re.search(r'\d+\s*[\+\-\*\/\^]\s*\d+', query))
        
        return has_keyword or has_numbers_and_ops

    def _extract_expression(self, query: str) -> Optional[str]:
        """
        Extract mathematical expression from query.
        
        Args:
            query: User's query
            
        Returns:
            Mathematical expression string or None
        """
        query_lower = query.lower()
        
        # Remove common prefixes
        prefixes = ['what is', 'what\'s', 'calculate', 'compute']
        for prefix in prefixes:
            if query_lower.startswith(prefix):
                query_lower = query_lower[len(prefix):].strip()
        
        # Replace word operators with symbols
        replacements = {
            ' plus ': '+',
            ' add ': '+',
            ' minus ': '-',
            ' subtract ': '-',
            ' times ': '*',
            ' multiply ': '*',
            ' multiplied by ': '*',
            ' divided by ': '/',
            ' divide ': '/',
            ' to the power of ': '**',
            ' squared': '**2',
            ' cubed': '**3',
        }
        
        for word, symbol in replacements.items():
            query_lower = query_lower.replace(word, symbol)
        
        # Extract the expression (numbers and operators)
        expression = re.sub(r'[^\d\+\-\*\/\.\(\)\^\*\s]', '', query_lower)
        expression = expression.replace('^', '**').strip()
        
        return expression if expression else None

    def calculate(self, query: str) -> str:
        """
        Process math query and return result.
        
        Args:
            query: User's query
            
        Returns:
            Calculation result as string
        """
        if not self._is_math_query(query):
            return None
        
        try:
            expression = self._extract_expression(query)
            
            if not expression:
                return "I couldn't understand that math expression. Try asking like 'what is 5 plus 3'."
            
            # Safely evaluate the expression
            # Note: eval is dangerous with untrusted input, but we've sanitized it
            result = eval(expression, {"__builtins__": {}}, {})
            
            # Format result
            if isinstance(result, float):
                # Show up to 4 decimal places, remove trailing zeros
                result_str = f"{result:.4f}".rstrip('0').rstrip('.')
            else:
                result_str = str(result)
            
            logger.info(f"Calculated: {expression} = {result_str}")
            return f"{expression} equals {result_str}"
        
        except ZeroDivisionError:
            return "I can't divide by zero."
        except Exception as e:
            logger.error(f"Error calculating: {e}")
            return "Sorry, I couldn't calculate that. Try rephrasing your question."
