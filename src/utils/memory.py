import json
import os
from typing import Dict, Optional
from datetime import datetime
from agno.storage.sqlite import SqliteStorage
from agno.utils import logger
from pydantic import BaseModel, Field


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


class Memory:
    def __init__(self, *args, session_id=None, storage=None, **kwargs):
        if storage is None:
            storage = SqliteStorage(
                table_name="publication_generation_workflow",
                db_file="tmp/publication_generated.db",
            )

        if session_id is not None:
            kwargs["storage"] = storage
        kwargs["storage"] = storage
        super().__init__(*args, **kwargs)
        self.final_publication_table = self.storage.get_table()
        logger.info("Ensured 'final_publication' table exists for permanent storage")

    # --- Explicit cache methods for each phase ---
    def get_cached_initial_prompt(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - initial_prompt phase")
        return self.session_state.get("initial_prompts", {}).get(topic)

    def add_initial_prompt_to_cache(self, topic: str, data: str):
        logger.debug(f"Caching initial prompt for topic '{topic}'")
        self.session_state.setdefault("initial_prompts", {})[topic] = data

    def get_cached_evaluation(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - evaluation phase")
        return self.session_state.get("evaluations", {}).get(topic)

    def add_evaluation_to_cache(self, topic: str, data: str):
        logger.debug(f"Caching evaluation for topic '{topic}'")
        self.session_state.setdefault("evaluations", {})[topic] = data

    def get_cached_improved_prompt(self, topic: str) -> Optional[str]:
        logger.debug(f"Checking cache for topic '{topic}' - improved_prompt phase")
        return self.session_state.get("improved_prompts", {}).get(topic)

    def add_improved_prompt_to_cache(self, topic: str, data: str):
        logger.debug(f"Caching improved prompt for topic '{topic}'")
        self.session_state.setdefault("improved_prompts", {})[topic] = data

    def save_final_publication(self, topic: str, publication: str) -> None:
        """Persist the *approved* publication in the long‑term SQLite store.

        If the topic already exists it will be *replaced* (upsert semantics).
        """
        # Store also in memory for quick access
        self.session_state.setdefault("final_publications", {})[topic] = publication

        try:
            # Use SqliteStorage helper if available
            if hasattr(self.final_publication_table, "insert"):
                # delete any existing row first (simple approach)
                try:
                    self.final_publication_table.delete().where(
                        self.final_publication_table.c.topic == topic
                    ).execute()
                except Exception:
                    # Might not exist – ignore
                    pass
                self.final_publication_table.insert(
                    {
                        "topic": topic,
                        "final_publication": publication,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ).execute()
            else:
                # Fallback – execute raw SQL
                sql = """CREATE TABLE IF NOT EXISTS final_publication (
                            topic TEXT PRIMARY KEY,
                            final_publication TEXT,
                            timestamp TEXT
                        );"""
                self.storage.execute(sql)
                upsert_sql = """INSERT OR REPLACE INTO final_publication (topic, final_publication, timestamp)
                               VALUES (?, ?, ?);"""
                self.storage.execute(
                    upsert_sql, (topic, publication, datetime.utcnow().isoformat())
                )
        except Exception as e:
            logger.error(f"Failed to save final publication for topic '{topic}': {e}")

    def get_final_publication(self, topic: str) -> Optional[Publication]:
        """Return a *Publication* record from permanent storage (or None)."""
        # Check in‑memory cache first
        if topic in self.session_state.get("final_publications", {}):
            return Publication(
                topic=topic,
                final_publication=self.session_state["final_publications"][topic],
            )

        try:
            if hasattr(self.final_publication_table, "select"):
                row = (
                    self.final_publication_table.select()
                    .where(self.final_publication_table.c.topic == topic)
                    .execute()
                    .fetchone()
                )
                if row:
                    return Publication(
                        topic=row["topic"],
                        final_publication=row["final_publication"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                    )
            else:
                sql = "SELECT topic, final_publication, timestamp FROM final_publication WHERE topic = ?;"
                cur = self.storage.execute(sql, (topic,))
                row = cur.fetchone()
                if row:
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
        publications = []
        try:
            if hasattr(self.final_publication_table, "select"):
                rows = (
                    self.final_publication_table.select()
                    .order_by(self.final_publication_table.c.timestamp.desc())
                    .limit(limit)
                    .offset(offset)
                    .execute()
                    .fetchall()
                )
                for r in rows:
                    publications.append(
                        Publication(
                            topic=r["topic"],
                            final_publication=r["final_publication"],
                            timestamp=datetime.fromisoformat(r["timestamp"]),
                        )
                    )
            else:
                sql = """SELECT topic, final_publication, timestamp
                         FROM final_publication ORDER BY timestamp DESC LIMIT ? OFFSET ?"""
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
        return publications

    def delete_final_publication(self, topic: str) -> bool:
        """Remove a publication from permanent storage. Returns *True* if deleted.*"""
        removed = False
        try:
            if hasattr(self.final_publication_table, "delete"):
                result = (
                    self.final_publication_table.delete()
                    .where(self.final_publication_table.c.topic == topic)
                    .execute()
                )
                removed = result.rowcount > 0 if hasattr(result, "rowcount") else True
            else:
                sql = "DELETE FROM final_publication WHERE topic = ?;"
                cur = self.storage.execute(sql, (topic,))
                removed = cur.rowcount > 0 if hasattr(cur, "rowcount") else True
        except Exception as e:
            logger.error(f"Error deleting final publication '{topic}': {e}")
        # Remove from in‑memory cache
        self.session_state.get("final_publications", {}).pop(topic, None)
        return removed

    # ---------- Session cache helpers ----------
    def get_cached_draft(self, topic: str) -> Optional[str]:
        return self.session_state.get("drafts", {}).get(topic)

    def add_draft_to_cache(self, topic: str, draft: str):
        self.session_state.setdefault("drafts", {})[topic] = draft

    def add_revision_to_cache(self, topic: str, content: str, iteration: int):
        revisions = self.session_state.setdefault("revisions", {}).setdefault(topic, [])
        revisions.append(
            {
                "iteration": iteration,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_revision_history(self, topic: str):
        return self.session_state.get("revisions", {}).get(topic, [])

    def mark_topic_as_approved(self, topic: str):
        self.session_state.setdefault("approvals", {})[topic] = True

    def is_topic_approved(self, topic: str) -> bool:
        return self.session_state.get("approvals", {}).get(topic, False)

    # ---------- Workflow status log ----------
    def log_status(self, agent: str, stage: str, timestamp: Optional[datetime] = None):
        timestamp = timestamp or datetime.utcnow()
        self.session_state.setdefault("status_log", []).append(
            {"agent": agent, "stage": stage, "timestamp": timestamp.isoformat()}
        )

    def get_status_log(self, topic: Optional[str] = None):
        # Currently no topic filtering; could be enhanced by including topic in log entries
        return self.session_state.get("status_log", [])

    # ---------- Utility helpers ----------
    def reset_session(self):
        self.session_state.clear()

    def topic_exists(self, topic: str) -> bool:
        return self.get_final_publication(topic) is not None

    def export_to_json(self, path: str):
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.session_state, f, ensure_ascii=False, indent=2)

    def import_from_json(self, path: str):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.session_state = json.load(f)
