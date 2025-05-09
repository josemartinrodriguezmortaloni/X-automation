from typing import Dict, Optional
from datetime import datetime
from agno.storage.sqlite import SqliteStorage
from agno.utils.log import logger
from pydantic import BaseModel, Field
from agno.memory import AgentMemory
import sqlite3


class Publication(BaseModel):
    """Model for storing the final generated publication permanently"""

    topic: str = Field(..., description="The original topic for the publication")
    final_publication: str = Field(
        ..., description="The final, improved and aproved publication."
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the publication was saved"
    )


class GenerataedPublication(BaseModel):
    """Model for storing generated publications"""

    publication: str = Field(..., description="Original topic publication")
    improved_publication: str = Field(..., description="Final and approved publication")


class PublicationEvaluation(BaseModel):
    """Model for storing publication evaluation"""

    publication: str = Field(..., description="The publication being evaluated")
    evaluation: Dict[str, str] = Field(..., description="Evaluation Results")
    recommedations: str = Field(..., description="Suggested improvments")
    approved: bool = Field(
        ..., description="If the publication is approved to be published"
    )


class Memory(AgentMemory):
    def __init__(self, *args, session_id=None, storage=None, **kwargs):
        if storage is None:
            storage = SqliteStorage(
                table_name="publication_generation_workflows",
                db_file="src/db/publication_generation.db",
            )
        if session_id is not None:
            kwargs["session_id"] = session_id
        kwargs["storage"] = storage
        super().__init__(*args, **kwargs)

        # Pydantic immutability workaround: attach storage & table explicitly
        object.__setattr__(self, "storage", storage)
        object.__setattr__(self, "final_prompts_table", storage.get_table())

        # Guarantee an in‑memory dict for caching if AgentMemory didn't create one
        if not hasattr(self, "session_state"):
            object.__setattr__(self, "session_state", {})

        logger.info("Ensured 'final_prompts' table exists for permanent storage.")

    # --- Explicit cache methods for each phase ---
    def get_cached_initial_publication(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - initial_publication phase")
        return self.session_state.get("initial_publications", {}).get(topic)

    def add_initial_publication_to_cache(self, topic: str, data: str):
        logger.debug(f"Caching initial publication for topic '{topic}'")
        self.session_state.setdefault("initial_publications", {})[topic] = data

    def get_planned_publication(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - planned_publication phase")
        return self.session_state.get("planned_publications", {}).get(topic)

    def add_planened_publication(self, topic: str, data: str):
        logger.debug(f"Caching planned publication for topic '{topic}'")
        self.session_state.setdefault("planned_publications", {})[topic] = data

    def get_cached_evaluation(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - evaluation phase")
        return self.session_state.get("evaluations", {}).get(topic)

    def add_evaluation_to_cache(self, topic: str, data: str):
        logger.debug(f"Caching evaluation for topic '{topic}'")
        self.session_state.setdefault("evaluations", {})[topic] = data

    def get_cached_improved_publication(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - improved_publication phase")
        return self.session_state.get("improved_publications", {}).get(topic)

    def add_improved_publication_to_cache(self, topic: str, data: str):
        logger.debug(f"Caching improved publication for topic '{topic}'")
        self.session_state.setdefault("improved_publications", {})[topic] = data

    def save_final_publication(self, topic: str, publication: str) -> None:
        """Upsert the approved publication into *final_prompts* table."""
        logger.debug(f"[Memory] save_final_publication called for topic: {topic}")
        # In-memory cache
        self.session_state.setdefault("final_publications", {})[topic] = publication
        logger.debug(
            f"[Memory] session_state final_publications updated for topic: {topic}"
        )

        try:
            logger.debug(
                f"[Memory] Connecting to SQLite DB for final_prompts upsert (topic={topic})"
            )
            # Use raw SQLite connection (works regardless of SQLAlchemy presence)
            # Determine DB file path from storage or default
            db_path = "src/db/publication_generation.db"
            logger.debug(f"[Memory] DB path set to {db_path}")

            conn = sqlite3.connect(db_path)
            logger.debug(f"[Memory] SQLite connection established at {db_path}")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS final_prompts (
                    topic TEXT PRIMARY KEY,
                    final_prompt TEXT,
                    timestamp TEXT
                );
                """
            )
            conn.execute(
                """INSERT OR REPLACE INTO final_prompts (topic, final_prompt, timestamp)
                   VALUES (?, ?, ?);""",
                (topic, publication, datetime.utcnow().isoformat()),
            )
            conn.commit()
            logger.debug(
                f"[Memory] commit successful for save_final_publication topic: {topic}"
            )
        except Exception as e:
            logger.error(f"Failed to save final publication for topic '{topic}': {e}")

    def get_final_publication(self, topic: str) -> Optional[Publication]:
        """Return a *Publication* record from permanent storage (or None)."""
        logger.debug(f"[Memory] get_final_publication called for topic: {topic}")
        # Check in-memory cache first
        if topic in self.session_state.get("final_publications", {}):
            logger.debug(
                f"[Memory] Final publication found in session_state for topic: {topic}"
            )
            return Publication(
                topic=topic,
                final_publication=self.session_state["final_publications"][topic],
            )

        try:
            logger.debug(
                f"[Memory] Querying DB for final_publication for topic: {topic}"
            )
            if hasattr(self.final_prompts_table, "select"):
                row = (
                    self.final_prompts_table.select()
                    .where(self.final_prompts_table.c.topic == topic)
                    .execute()
                    .fetchone()
                )
                if row:
                    logger.debug(
                        f"[Memory] Retrieved final_publication from table for topic: {topic}"
                    )
                    return Publication(
                        topic=row["topic"],
                        final_publication=row["final_prompt"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                    )
            else:
                logger.debug(
                    f"[Memory] Using raw SQL to fetch final_publication for topic: {topic}"
                )
                sql = "SELECT topic, final_prompt, timestamp FROM final_prompts WHERE topic = ?;"
                cur = self.storage.execute(sql, (topic,))
                row = cur.fetchone()
                if row:
                    logger.debug(
                        f"[Memory] Retrieved final_publication via raw SQL for topic: {topic}"
                    )
                    return Publication(
                        topic=row[0],
                        final_publication=row[1],
                        timestamp=datetime.fromisoformat(row[2]),
                    )
        except Exception as e:
            logger.error(f"Error fetching final publication for topic '{topic}': {e}")
        return None

    def list_final_publications(self, limit: int = 50, offset: int = 0):
        """Return a list of *Publication* objects ordered by timestamp desc."""
        logger.debug(
            f"[Memory] list_final_publications called with limit={limit}, offset={offset}"
        )
        publications = []
        try:
            if hasattr(self.final_prompts_table, "select"):
                rows = (
                    self.final_prompts_table.select()
                    .order_by(self.final_prompts_table.c.timestamp.desc())
                    .limit(limit)
                    .offset(offset)
                    .execute()
                    .fetchall()
                )
                for r in rows:
                    publications.append(
                        Publication(
                            topic=r["topic"],
                            final_publication=r["final_prompt"],
                            timestamp=datetime.fromisoformat(r["timestamp"]),
                        )
                    )
            else:
                sql = """SELECT topic, final_prompt, timestamp
                         FROM final_prompts ORDER BY timestamp DESC LIMIT ? OFFSET ?"""
                cur = self.storage.execute(sql, (limit, offset))
                for row in cur.fetchall():
                    publications.append(
                        Publication(
                            topic=row[0],
                            final_publication=row[1],
                            timestamp=datetime.fromisoformat(row[2]),
                        )
                    )
        except Exception as e:
            logger.error(f"Error listing final publications: {e}")
        logger.debug(
            f"[Memory] list_final_publications returning {len(publications)} publications"
        )
        return publications

    def delete_final_publication(self, topic: str) -> bool:
        """Remove a publication from permanent storage. Returns *True* if deleted.*"""
        logger.debug(f"[Memory] delete_final_publication called for topic: {topic}")
        removed = False
        try:
            if hasattr(self.final_prompts_table, "delete"):
                result = (
                    self.final_prompts_table.delete()
                    .where(self.final_prompts_table.c.topic == topic)
                    .execute()
                )
                removed = result.rowcount > 0 if hasattr(result, "rowcount") else True
            else:
                sql = "DELETE FROM final_prompts WHERE topic = ?;"
                cur = self.storage.execute(sql, (topic,))
                removed = cur.rowcount > 0 if hasattr(cur, "rowcount") else True
        except Exception as e:
            logger.error(f"Error deleting final publication '{topic}': {e}")
        # Remove from in-memory cache
        pop_result = self.session_state.get("final_publications", {}).pop(topic, None)
        logger.debug(
            f"[Memory] session_state.pop returned {pop_result!r} for topic: {topic}"
        )
        return removed
