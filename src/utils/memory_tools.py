from agno.tools import Toolkit
from typing import Optional
from agno.utils.log import logger

from .memory import Memory

# Instantiate a single Memory backend that can be reused by all tool calls.
# This ensures every agent in the Team sees the same session state.
_shared_memory = Memory(session_id="publication-team")


class MemoryTools(Toolkit):
    """Expose helper methods that delegate to src.utils.memory.Memory
    so that agents can cache drafts, evaluations, revisions and persist
    final publications via tool calls.
    """

    def __init__(self):
        super().__init__(name="memory_tools")

        # Register public methods as tools
        self.register(self.add_draft)
        self.register(self.add_evaluation)
        self.register(self.add_revision)
        self.register(self.save_final_publication)
        self.register(self.get_draft)
        self.register(self.get_evaluation)
        self.register(self.mark_approved)

    # ----------------- write helpers -----------------
    def add_draft(self, topic: str, draft: str) -> str:
        """Cache a first draft for *topic*."""
        _shared_memory.add_draft_to_cache(topic, draft)
        logger.info(f"Draft cached for topic '{topic}'")
        return "draft_cached"

    def add_evaluation(self, topic: str, evaluation: str) -> str:
        """Store evaluator feedback for a *topic*."""
        _shared_memory.add_evaluation_to_cache(topic, evaluation)
        return "evaluation_cached"

    def add_revision(self, topic: str, content: str, iteration: int) -> str:
        """Save a revised draft along with its iteration number."""
        _shared_memory.add_revision_to_cache(topic, content, iteration)
        return "revision_cached"

    def save_final_publication(self, topic: str, content: str) -> str:
        """Persist the final approved publication to the DB and memory."""
        _shared_memory.save_final_publication(topic, content)
        return "publication_saved"

    def mark_approved(self, topic: str) -> str:
        """Mark a topic as approved after positive evaluation."""
        _shared_memory.mark_topic_as_approved(topic)
        return "topic_marked_approved"

    # ----------------- read helpers ------------------
    def get_draft(self, topic: str) -> str:
        """Return cached draft if it exists; else empty string."""
        return _shared_memory.get_cached_draft(topic) or ""

    def get_evaluation(self, topic: str) -> str:
        """Return cached evaluation if it exists; else empty string."""
        return _shared_memory.get_cached_evaluation(topic) or ""
