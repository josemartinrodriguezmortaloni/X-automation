import json
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Workflow, RunResponse, RunEvent
from dotenv import load_dotenv
from ..utils.tools import FileSystemTools
from agno.utils.log import logger
from ..utils.memory import Memory
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Iterator
from ..utils.knowledge import Knowledge
from ..utils.prompt_loader import PromptLoader

load_dotenv()


class Publication(BaseModel):
    """Model for storing the final generated publication permanently"""

    topic: str = Field(..., description="The original topic for the publication")
    final_publication: str = Field(
        ..., description="The final, improved and aproved publication."
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the publication was saved"
    )


class PublicationWorkflow(Workflow):
    """Workflow for generating publications and chatting through dms for x using ia"""

    orchestrator: Agent = Agent(
        name="Orchestrator",
        role="Orchestrate all the members of the content creation team",
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=lambda *args, **kwargs: PromptLoader.load(
            "orchestrator", knowledge_desc=Knowledge.knowledge_base
        ),
        knowledge=Knowledge.knowledge_base,
        search_knowledge=True,
        markdown=True,
        show_tool_calls=True,
    )

    publication_writer: Agent = Agent(
        name="Writer",
        role="ByteWriter-X, the content engine for BytesBricks AI",
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=lambda *args, **kwargs: PromptLoader.load(
            "instrucciones", plan="${plan}", num_posts="${num_posts}"
        ),
        reasoning=False,
        tools=[FileSystemTools()],
        knowledge=Knowledge.knowledge_base,
        search_knowledge=True,
        markdown=True,
        show_tool_calls=True,
    )
    publication_evaluator: Agent = Agent(
        name="Evaluator",
        role="Assesses drafts and decides Publish / Do Not Publish with actionable feedback",
        model=OpenAIResponses(id="o4-mini"),
        instructions=lambda *args, **kwargs: PromptLoader.load("evaluator"),
        knowledge=Knowledge.knowledge_base,
        search_knowledge=True,
        reasoning=False,
        markdown=True,
        show_tool_calls=True,
    )
    publication_publisher: Agent = Agent(
        name="Publisher",
        role="Formats and publishes the approved content to X, returning confirmation",
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=lambda *args, **kwargs: PromptLoader.load("publisher"),
        knowledge=Knowledge.knowledge_base,
        search_knowledge=True,
        tools=[FileSystemTools()],
        markdown=True,
        show_tool_calls=True,
    )

    # --- Cache methods fro each phase --- #
    def get_cached_initial_publication(topic: str) -> Optional[str]:
        session_state = Memory.get_cached_initial_publication(topic)
        return session_state

    def add_initial_publication_to_cache(topic: str, data: str):
        add_draft_to_cache = Memory.add_initial_publication_to_cache(topic, data)
        return add_draft_to_cache

    def get_planned_publication(self, topic: str) -> Optional[str]:
        planned_publication = Memory.get_planned_publication(topic)
        return planned_publication

    def add_planened_publication(self, topic: str, data: str):
        add_planened_publication = Memory.add_planened_publication(topic, data)
        return add_planened_publication

    def get_cached_evaluation(topic: str) -> Optional[str]:
        cached_evaluation = Memory.get_cached_evaluation(topic)
        return cached_evaluation

    def add_evaluation_to_cache(topic: str, data: str):
        add_evaluation = Memory.add_evaluation_to_cache(topic, data)
        return add_evaluation

    def get_cached_improved_publication(topic: str) -> Optional[str]:
        cached_improved_publication = Memory.get_cached_improved_publication(topic)
        return cached_improved_publication

    def add_improved_publication_to_cache(topic: str, data: str):
        add_improved_publication_to_cache = Memory.add_improved_publication_to_cache(
            topic, data
        )
        return add_improved_publication_to_cache

    def save_final_publication(topic: str, publication: str) -> None:
        final_publication_saved = Memory.save_final_publication(topic, publication)
        return final_publication_saved

    def get_final_publication(self, topic: str) -> Optional[Publication]:
        final_publication = Memory.get_final_publication(topic)
        return final_publication

    def list_final_publications(self, limit: int = 50, offset: int = 0):
        final_publications = Memory.list_final_publications(limit, offset)
        return final_publications

    def delete_final_publication(self, topic: str) -> bool:
        delete_publication = Memory.delete_final_publication(topic)
        return delete_publication

    def __init__(self, session_id: str | None = None):
        super().__init__(session_id=session_id)
        # Shared memory backend for this workflow
        self.memory: Memory = Memory(session_id=session_id)

    def run(
        self,
        topic: str,
        use_cache: bool = True,
        max_revisions: int = 10,
        num_posts: int = 1,
    ) -> Iterator[RunResponse]:
        """End‑to‑end publication workflow.

        Fases:
        0. Plan – Orchestrator diseña la estructura del contenido.
        1. Draft – Writer genera contenido inicial según el plan.
        2. Evaluation – Evaluator revisa; si *no* aprueba, Writer revisa (loop).
        3. Publish – Publisher formatea/publica; se persiste la versión final.
        """
        logger.info(f"Publication workflow for topic '{topic}' (cache={use_cache})")
        logger.debug(
            f"[Workflow] Attempting to retrieve planned publication from memory (use_cache={use_cache}) for topic: {topic}"
        )
        plan = self.memory.get_planned_publication(topic) if use_cache else None
        logger.debug(f"[Workflow] Retrieved plan: {'CACHED' if plan else 'NONE'}")
        if plan:
            yield RunResponse(
                content=f"# 0. Plan (cached)\n\n{plan}", event=RunEvent.run_response
            )
        else:
            plan_prompt = {
                "topic": topic,
                "task": "Design an outline/plan for an engaging thread for X",
                "requirements": {"format": "markdown", "structure": "sections"},
            }
            try:
                plan_resp = self.orchestrator.run(
                    json.dumps(plan_prompt, indent=4), stream=False
                )
                plan = plan_resp.content
                self.memory.add_planened_publication(topic, plan)
                yield RunResponse(
                    content=f"# 0. Plan\n\n{plan}", event=RunEvent.run_response
                )
            except Exception as e:
                logger.error(f"Plan generation failed: {e}")
                yield RunResponse(
                    content=f"Error during plan generation: {e}",
                    event=RunEvent.run_error,
                )
                return

        # ---------------- 1) DRAFT ---------------- #
        logger.debug(
            f"[Workflow] Attempting to retrieve initial draft from memory (use_cache={use_cache}) for topic: {topic}"
        )
        draft = self.memory.get_cached_initial_publication(topic) if use_cache else None
        logger.debug(f"[Workflow] Retrieved draft: {'CACHED' if draft else 'NONE'}")
        if draft:
            yield RunResponse(
                content=f"# 1. Draft (cached)\n\n{draft}",
                event=RunEvent.run_response,
            )
        else:
            writer_prompt = {
                "plan": plan,
                "num_posts": num_posts,
            }
            try:
                draft_resp = self.publication_writer.run(
                    json.dumps(writer_prompt, indent=4), stream=False
                )
                draft = draft_resp.content
                self.memory.add_initial_publication_to_cache(topic, draft)
                logger.debug(
                    f"[Workflow] Initial draft saved to memory for topic: {topic}"
                )
                yield RunResponse(
                    content=f"# 1. Draft\n\n{draft}", event=RunEvent.run_response
                )
            except Exception as e:
                logger.error(f"Draft generation failed: {e}")
                yield RunResponse(
                    content=f"Error during draft generation: {e}",
                    event=RunEvent.run_error,
                )
                return

        # ---------------- 2) EVALUACIÓN & REVISIONES ---------------- #
        approved = False
        iteration = 0
        while not approved and iteration < max_revisions:
            evaluation = (
                self.memory.get_cached_evaluation(topic)
                if use_cache and iteration == 0
                else None
            )
            logger.debug(
                f"[Workflow] Retrieved evaluation: {'CACHED' if evaluation else 'NONE'}"
            )
            if not evaluation:
                eval_prompt = {
                    "draft": draft,
                    "task": "Evaluate the draft. Reply 'Publish' or provide feedback.",
                }
                try:
                    eval_resp = self.publication_evaluator.run(
                        json.dumps(eval_prompt, indent=4), stream=False
                    )
                    evaluation = eval_resp.content
                    self.memory.add_evaluation_to_cache(topic, evaluation)
                    logger.debug(
                        f"[Workflow] Evaluation saved to memory for topic: {topic}"
                    )
                except Exception as e:
                    logger.error(f"Evaluation failed: {e}")
                    yield RunResponse(
                        content=f"Error during evaluation: {e}",
                        event=RunEvent.run_error,
                    )
                    return
            yield RunResponse(
                content=f"# 2.{iteration} Evaluation\n\n{evaluation}",
                event=RunEvent.run_response,
            )

            # Determine approval status strictly:
            eval_lower = evaluation.lower()
            positive = any(word in eval_lower for word in ("publish", "approved"))
            negative = any(
                phrase in eval_lower
                for phrase in ("do not publish", "revision_required", "do not publish")
            )
            if positive and not negative:
                approved = True
                break

            # Solicitar revisión al Writer
            iteration += 1
            rewrite_prompt = {
                "draft": draft,
                "feedback": evaluation,
                "task": "Rewrite the draft addressing all feedback points.",
            }
            try:
                rev_resp = self.publication_writer.run(
                    json.dumps(rewrite_prompt, indent=4), stream=False
                )
                draft = rev_resp.content
                self.memory.add_improved_publication_to_cache(topic, draft)
                logger.debug(
                    f"[Workflow] Improved draft saved to memory for topic: {topic}"
                )
                yield RunResponse(
                    content=f"# 2.{iteration} Revision\n\n{draft}",
                    event=RunEvent.run_response,
                )
            except Exception as e:
                logger.error(f"Revision failed: {e}")
                yield RunResponse(
                    content=f"Error during revision: {e}", event=RunEvent.run_error
                )
                return

        if not approved:
            logger.warning("Maximum revision iterations reached without approval")

        # ---------------- 3) PUBLICACIÓN ---------------- #
        publish_prompt = {
            "content": draft,
            "task": "Format and publish the thread; save markdown using write_file.",
        }
        try:
            pub_resp = self.publication_publisher.run(
                json.dumps(publish_prompt, indent=4), stream=False
            )
            published = pub_resp.content
            self.memory.save_final_publication(topic, published)
            logger.debug(
                f"[Workflow] Final publication saved to memory for topic: {topic}"
            )
            yield RunResponse(
                content=f"# 3. Published\n\n{published}", event=RunEvent.run_response
            )
        except Exception as e:
            logger.error(f"Publication failed: {e}")
            yield RunResponse(
                content=f"Error during publication: {e}", event=RunEvent.run_error
            )
