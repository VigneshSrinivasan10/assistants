"""
Smart conversation memory with quality filtering and relevance scoring.
Much better than just "last N conversations".
"""
import json
import os
import re
from collections import deque
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationQuality:
    """Scores conversation quality."""
    
    @staticmethod
    def score(user_msg: str, assistant_msg: str, handler: Optional[str] = None) -> float:
        """
        Score conversation quality (0.0 - 1.0).
        
        Args:
            user_msg: User's message
            assistant_msg: Assistant's response
            handler: Which handler processed it (Weather, Spotify, LLM, etc.)
            
        Returns:
            Quality score (higher = better)
        """
        score = 0.5  # Base score
        
        # Penalize very short exchanges (likely errors or noise)
        if len(user_msg) < 3 or len(assistant_msg) < 10:
            score -= 0.3
        
        # Penalize error messages
        error_keywords = ['sorry', 'couldn\'t', 'error', 'failed', 'can\'t']
        if any(kw in assistant_msg.lower() for kw in error_keywords):
            score -= 0.2
        
        # Boost complete exchanges
        if len(user_msg) > 10 and len(assistant_msg) > 20:
            score += 0.2
        
        # Boost specific handlers (they tend to be higher quality)
        if handler and handler != "LLM":
            score += 0.15
        
        # Boost questions (more likely to be important)
        if '?' in user_msg:
            score += 0.1
        
        # Penalize repetitive responses
        repetitive_phrases = [
            "I don't understand",
            "I'm not sure",
            "Could you rephrase",
        ]
        if any(phrase.lower() in assistant_msg.lower() for phrase in repetitive_phrases):
            score -= 0.15
        
        # Clamp to 0-1 range
        return max(0.0, min(1.0, score))


class RelevanceScorer:
    """Scores conversation relevance using simple keyword matching."""
    
    @staticmethod
    def compute_relevance(query: str, conversation: Dict) -> float:
        """
        Compute relevance of a past conversation to current query.
        
        Args:
            query: Current user query
            conversation: Past conversation dict
            
        Returns:
            Relevance score (0.0 - 1.0)
        """
        query_words = set(re.findall(r'\w+', query.lower()))
        
        # Get words from past conversation
        user_words = set(re.findall(r'\w+', conversation['user'].lower()))
        assistant_words = set(re.findall(r'\w+', conversation['assistant'].lower()))
        conv_words = user_words | assistant_words
        
        # Remove common stop words (simplified list)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can',
            'what', 'how', 'when', 'where', 'why', 'who', 'which',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your'
        }
        
        query_words -= stop_words
        conv_words -= stop_words
        
        if not query_words or not conv_words:
            return 0.0
        
        # Jaccard similarity
        intersection = query_words & conv_words
        union = query_words | conv_words
        
        return len(intersection) / len(union) if union else 0.0


class SmartConversationMemory:
    """
    Smart conversation memory with quality filtering and relevance scoring.
    
    Features:
    - Quality filtering (removes errors, short exchanges, etc.)
    - Relevance scoring (includes old but relevant conversations)
    - Recency bias (recent conversations weighted higher)
    - Token budget (prevents context overflow)
    - Deduplication (removes similar conversations)
    """
    
    def __init__(
        self,
        max_context_tokens: int = 1000,
        quality_threshold: float = 0.3,
        relevance_threshold: float = 0.2,
        save_file: str = "./data/conversation_memory.json",
        max_stored: int = 100,
    ):
        """
        Initialize smart memory.
        
        Args:
            max_context_tokens: Max tokens to include in context (~4 chars = 1 token)
            quality_threshold: Minimum quality score to include (0.0-1.0)
            relevance_threshold: Minimum relevance score for old conversations
            save_file: Path to save conversations
            max_stored: Max conversations to keep in storage
        """
        self.max_context_tokens = max_context_tokens
        self.quality_threshold = quality_threshold
        self.relevance_threshold = relevance_threshold
        self.max_stored = max_stored
        
        # Storage (most recent first)
        self.conversations = deque(maxlen=max_stored)
        
        # File path
        project_root = Path(__file__).parents[1]
        self.save_file = str((project_root / save_file).resolve())
        
        # Scorers
        self.quality_scorer = ConversationQuality()
        self.relevance_scorer = RelevanceScorer()
        
        # Load existing
        self.load_memory()
        
        logger.info(
            f"SmartMemory initialized: max_tokens={max_context_tokens}, "
            f"quality_threshold={quality_threshold}, "
            f"relevance_threshold={relevance_threshold}"
        )
    
    def add_conversation(
        self,
        user_message: str,
        assistant_response: str,
        handler: Optional[str] = None
    ):
        """
        Add conversation with quality scoring.
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            handler: Handler that processed it (optional)
        """
        # Compute quality score
        quality = self.quality_scorer.score(user_message, assistant_response, handler)
        
        conversation = {
            "user": user_message,
            "assistant": assistant_response,
            "handler": handler,
            "quality": quality,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Only add if quality meets threshold
        if quality >= self.quality_threshold:
            self.conversations.appendleft(conversation)  # Most recent first
            logger.debug(
                f"Added conversation (quality={quality:.2f}, handler={handler}): "
                f"'{user_message[:50]}...'"
            )
        else:
            logger.debug(
                f"Skipped low-quality conversation (quality={quality:.2f}): "
                f"'{user_message[:50]}...'"
            )
        
        # Save periodically (every 5 additions)
        if len(self.conversations) % 5 == 0:
            self.save_memory()
    
    def get_context(self, current_query: Optional[str] = None) -> str:
        """
        Get smart context for LLM.
        
        Strategy:
        1. Always include recent high-quality conversations (last ~5)
        2. Include older relevant conversations if query provided
        3. Respect token budget
        
        Args:
            current_query: Current user query (for relevance scoring)
            
        Returns:
            Formatted context string
        """
        if not self.conversations:
            return ""
        
        selected = []
        token_count = 0
        
        # Phase 1: Recent conversations (recency bias)
        recent_count = min(5, len(self.conversations))
        for conv in list(self.conversations)[:recent_count]:
            tokens = self._estimate_tokens(conv)
            if token_count + tokens <= self.max_context_tokens:
                selected.append(conv)
                token_count += tokens
            else:
                break
        
        # Phase 2: Relevant older conversations (if query provided)
        if current_query and token_count < self.max_context_tokens:
            # Score all remaining conversations by relevance
            remaining = list(self.conversations)[recent_count:]
            scored = [
                (conv, self.relevance_scorer.compute_relevance(current_query, conv))
                for conv in remaining
            ]
            
            # Sort by relevance (highest first)
            scored.sort(key=lambda x: x[1], reverse=True)
            
            # Add relevant ones until token budget exhausted
            for conv, relevance in scored:
                if relevance < self.relevance_threshold:
                    break
                
                tokens = self._estimate_tokens(conv)
                if token_count + tokens <= self.max_context_tokens:
                    selected.append(conv)
                    token_count += tokens
                    logger.debug(
                        f"Added relevant old conversation (rel={relevance:.2f}): "
                        f"'{conv['user'][:50]}...'"
                    )
                else:
                    break
        
        # Format context
        return self._format_context(selected)
    
    def _estimate_tokens(self, conversation: Dict) -> int:
        """Estimate tokens in a conversation (~4 chars = 1 token)."""
        text = conversation['user'] + conversation['assistant']
        return len(text) // 4
    
    def _format_context(self, conversations: List[Dict]) -> str:
        """Format conversations for LLM context."""
        if not conversations:
            return ""
        
        # Sort by timestamp (oldest first for context)
        sorted_convs = sorted(
            conversations,
            key=lambda c: c.get('timestamp', '')
        )
        
        parts = []
        for conv in sorted_convs:
            parts.append(f"<|user|>\n{conv['user']}\n<|end|>")
            parts.append(f"<|assistant|>\n{conv['assistant']}\n<|end|>")
        
        return "\n".join(parts)
    
    def save_memory(self):
        """Save conversations to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.save_file), exist_ok=True)
            
            # Convert deque to list for JSON
            conv_list = list(self.conversations)
            
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "conversations": conv_list,
                    "config": {
                        "max_context_tokens": self.max_context_tokens,
                        "quality_threshold": self.quality_threshold,
                        "relevance_threshold": self.relevance_threshold,
                    }
                }, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(conv_list)} conversations to {self.save_file}")
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def load_memory(self):
        """Load conversations from file."""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                conv_list = data.get("conversations", [])
                
                # Load into deque (maintain order - most recent first)
                for conv in conv_list:
                    self.conversations.append(conv)
                
                logger.info(f"Loaded {len(conv_list)} conversations from {self.save_file}")
            else:
                logger.info("No existing memory file, starting fresh")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
    
    def get_memory_info(self) -> dict:
        """Get memory statistics."""
        if not self.conversations:
            return {
                "total_conversations": 0,
                "avg_quality": 0.0,
                "quality_distribution": {},
                "handlers": {},
            }
        
        qualities = [c['quality'] for c in self.conversations]
        handlers = {}
        for c in self.conversations:
            h = c.get('handler', 'Unknown')
            handlers[h] = handlers.get(h, 0) + 1
        
        # Quality distribution
        quality_dist = {
            "high (>0.7)": sum(1 for q in qualities if q > 0.7),
            "medium (0.5-0.7)": sum(1 for q in qualities if 0.5 <= q <= 0.7),
            "low (<0.5)": sum(1 for q in qualities if q < 0.5),
        }
        
        return {
            "total_conversations": len(self.conversations),
            "avg_quality": sum(qualities) / len(qualities),
            "min_quality": min(qualities),
            "max_quality": max(qualities),
            "quality_distribution": quality_dist,
            "handlers": handlers,
            "save_file": self.save_file,
        }
    
    def clear(self):
        """Clear all conversations."""
        self.conversations.clear()
        self.save_memory()
        logger.info("Memory cleared")
