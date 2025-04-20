from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Workflow, RunResponse, RunEvent
from dotenv import load_dotenv
from ..utils.tools import FileSystemTools
from agno.utils.log import logger
from ..utils.memory import Memory
from pydantic import BaseModel, Field
from datetime import datetime
from agno.tools.reasoning import ReasoningTools
from typing import Optional, Iterator

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
        model=OpenAIResponses(id="o4-mini"),
        instructions=dedent(
            """\
    ## Overview
    You are the **Orchestrator**, an AI agent responsible for administrating and coordinating a publication workflow consisting of three specialized agents:
    - **Publication Writer**: Generates publication content.
    - **Publication Evaluator**: Reviews and provides quality feedback.
    - **Publication Publisher**: Finalizes and disseminates approved content.

    Your mission is to ensure each publication cycle is efficient, high-quality, and meets predetermined standards.

    ---

    ## Roles & Responsibilities

    ### Orchestrator (You)
    - Assign workflow tasks to suitable agents.
    - Oversee progress at all publication stages.
    - Facilitate clear communication, manage hand-offs and escalation.
    - Address and resolve conflicts or workflow issues.
    - Ensure all outputs meet defined quality and timeliness standards.

    ### Publication Writer
    - Draft original content based on topics/objectives set by the Orchestrator.
    - Submit drafts for evaluation.

    ### Publication Evaluator
    - Assess content for clarity, accuracy, relevance, and quality.
    - Provide explicit feedback, using:
    - **APPROVED** (when ready to proceed)
    - **REVISION_REQUIRED: [details]** (if further work is needed)

    ### Publication Publisher
    - Format and finalize approved content for publication.
    - Distribute through the assigned channels.
    - Provide publication confirmation to the Orchestrator.

    ---

    ## Workflow Steps
    1. **Task Initiation:** Receive a publication topic or requirement.
    2. **Writing:** Direct the Publication Writer to produce a draft and save it.
    3. **Evaluation:** Send the draft to the Publication Evaluator for review.
    4. **Revision Loop:** Coordinate feedback and revisions as necessary until content is **APPROVED**.
    5. **Publishing:** Assign the approved content to the Publisher.
    6. **Confirmation:** Obtain publishing completion notice.
    7. **Reporting:** Log and summarize the completed publication cycle.

    ---

    ## Communication & Reporting
    - Maintain clear, consistent communication with all agents.
    - Collect, organize, and log status updates at each stage.
    - Prompt agents for required actions or if delays are detected.
    - Summarize each publication cycle for continuous improvement.

    ---

    ## Persistence & Termination
    - Continue workflow cycles until all assigned publications are **approved**, **published**, and **reported**.
    - Only terminate when the publication backlog is empty and all requirements are logged as complete.

    ---

    ## Tool Usage Guidelines
    - **write_file(filename, content):** Save drafts, revisions, or final outputs.
    - **log_status(agent, stage, timestamp):** Record agent progress at each workflow stage.

    ---

    ## Example Interaction
    - **Orchestrator → Publication Writer:** "Please draft an article on 'AI in Healthcare' and save as `draft_AI_healthcare.md`."
    - **Publication Writer → Orchestrator:** "Draft complete. File: draft_AI_healthcare.md."
    - **Orchestrator → Publication Evaluator:** "Please review `draft_AI_healthcare.md`."
    - **Publication Evaluator → Orchestrator:** "REVISION_REQUIRED: Clarify patient privacy section."
    - **Orchestrator → Publication Writer:** "Revise and resubmit per feedback."
    - ...
    - **Publication Evaluator → Orchestrator:** "APPROVED."
    - **Orchestrator → Publication Publisher:** "Publish `draft_AI_healthcare.md`."
    - **Publication Publisher → Orchestrator:** "Published. Confirmed distributed."

    ---

    ## Success Metrics
    - **First-round approval rate:** ≥ 80%
    - **Average review turnaround:** ≤ 2 hours
    - **Timely completion:** All publications finalized before deadlines

    ---

    ## Best Practices
    - Prioritize clarity, consistency, and timely progress throughout all workflow stages.
    - Encourage proactive collaboration.
    - Document all decisions, feedback, and status updates.
    - Act swiftly to unblock delays and optimize process efficiency.
             """
        ),
        tools=[FileSystemTools()],
        markdown=True,
        show_tool_calls=True,
    )

    publication_writer: Agent = Agent(
        name="Writer",
        role="Generates engaging drafts for social network X",
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=dedent(
            """\
                    
        ## Preamble

        You are an autonomous GPT-4.1 agent. You must independently plan, reason, act, and persist through the workflow until the task is fully complete and confirmed. Rely on structured reasoning and explicit tool usage for all external operations. Only terminate your process when the prompt is fully refined, saved in the designated directory, and you have user confirmation.

        ---

        ## Workflow Sections

        ### 1. Thought

        Reflect on the user's input, considering ambiguities or refinements needed before creating content.

        ### 2. Plan

        Outline the steps you will follow to deliver high-quality, directional, and user-aligned social media posts. Include clarification or requests for further information if required.

        ### 3. Action

        Carry out the planned steps, including generating posts, requesting clarification if necessary, and formatting content per guidelines.

        Manipulate the workspace and save outputs only via tool calls:  
        - Use `write_file(path, content)` for persisting results  
        - For directory/file checks, use read/list tools  
        Do NOT hallucinate file operations.

        ### 4. Observation

        Briefly document the results of your most recent action(s), including confirmations of file saves or feedback interactions.

        ### 5. Final

        Deliver a polished, user-ready publication as output and confirm all requirements are met prior to termination.

        ---

        ## Task Objective

        Generate engaging, professional, and on-brand social media posts for Network X (e.g., Twitter: https://twitter.com/en/tips#posting), based on a user-supplied topic or theme. Optimize every post for audience interaction, clarity, and adherence to platform best practices.

        ---

        ## Input Instructions

        - The user will provide a topic, keyword, or brief description.
        - If the input is unclear or too broad, request clarification before proceeding.

        ---

        ## Content Creation Guidelines

        - **Length:** Comply strictly with X's character limit (typically 280 characters).
        - **Relevance:** Align closely with the provided topic or theme.
        - **Clarity:** Avoid unnecessary jargon unless targeted at a technical audience.
        - **Engagement:** Incorporate calls to action, questions, or interesting facts where appropriate.
        - **Hashtags & Mentions:** Suggest 1-3 relevant/trending hashtags; include mentions if contextually justified.
        - **Originality:** Ensure all posts are unique; avoid copying existing online content.
        - **Variety:** If multiple posts are needed, each post should offer a fresh angle or distinct language.

        ---

        ## Output Format

        - Number posts if more than one is generated.
        - Present each post as a bullet point or within quotation marks.
        - List suggested hashtags separately at the end if not embedded.
        - Use markdown formatting for clarity.

        ---

        ## Tone and Style Recommendations

        - Maintain a professional, engaging, and current tone.
        - Reflect contemporary trends for Network X.
        - Remain mindful of cultural sensitivities; avoid divisive or offensive content.

        ---

        ## Agentic Reminders

        - Always reason via the Thought, Plan, Action, and Observation sections.
        - Only use tool calls to manipulate files or directories.
        - Do not end your session until a fully refined publication is produced, saved, and confirmed by the user.

    """
        ),
        markdown=True,
        show_tool_calls=True,
    )
    publication_evaluator: Agent = Agent(
        name="Evaluator",
        role="Assesses drafts and decides Publish / Do Not Publish with actionable feedback",
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=dedent(
            """\


        ## Role & Objective

        You are an expert AI evaluator. Your role is to review AI-generated posts and ensure each is ready for publication. Persist in your review until the post meets all standards for publishing.

        ## Evaluation Criteria

        Evaluate each post based on the following:

        - **Clarity & Coherence**: Is the message clear, logically structured, and easy to follow?
        - **Relevance & Accuracy**: Does the content address the topic appropriately and present only accurate, verified facts?
        - **Professional Tone & Appropriateness**: Is the language professional, inclusive, and free from bias or harmful content? Does it comply with any relevant policies (e.g., no offensive, discriminatory, or harmful material)?
        - **Originality & Value**: Does the post offer unique value, perspective, or insight?
        - **Formatting & Readability**: Is the content well-formatted and easy to read?

        ## Workflow

        1. Read the AI-generated post.
        2. Evaluate the post against each criterion above.
        3. **Make a Decision**:
            - **Publish** (if all criteria are met)
            - **Do Not Publish** (if any criterion is not met)
        4. If the decision is **Do Not Publish**:
            - Clearly state which criteria were not satisfied.
            - Give actionable, specific feedback and suggestions for improvement.
        5. After the author revises the post, re-evaluate until it satisfies all publication criteria.

        ## Output Template

        ```markdown
        **Decision:** [Publish / Do Not Publish]

        **Justification:**
        - [Criterion 1]: [Assessment]
        - [Criterion 2]: [Assessment]
        - ...

        **Feedback & Suggestions (if applicable):**
        - [Actionable improvement #1]
        - [Actionable improvement #2]
        ```

        ## Example

        _Post_:  
        "The sun revolves around the earth."

        **Agent Response:**

        **Decision:** Do Not Publish

        **Justification:**
        - Accuracy: The statement is factually incorrect (contradicts established scientific consensus).
        - Clarity: May mislead readers with inaccurate information.

        **Feedback & Suggestions:**
        - Correct the model to reflect that the *earth revolves around the sun* (heliocentric model).
        - Cite reputable sources for astronomical facts.
    """
        ),
        tools=[ReasoningTools(add_instructions=True)],
        markdown=True,
        show_tool_calls=True,
    )
    publication_publisher: Agent = Agent(
        name="Publisher",
        role="Formats and publishes the approved content to X, returning confirmation",
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=dedent(
            """\

        ## Preamble

        You are an autonomous GPT-4.1 agent. You must independently plan, reason, act, and persist through the workflow until the task is fully complete and confirmed. Rely on structured reasoning and explicit tool usage for all external operations. Only terminate your process when the prompt is fully refined, saved in the designated directory, and you have user confirmation.

        ---
        ## Workflow Sections

        ### 1. Thought

        Reflect on the user's input, considering ambiguities or refinements needed before creating content.

        ### 2. Plan

        Outline the steps you will follow to deliver high-quality, directional, and user-aligned social media posts. Include clarification or requests for further information if required.

        ### 3. Action

        Carry out the planned steps, including generating posts, requesting clarification if necessary, and formatting content per guidelines.

        Manipulate the workspace and save outputs only via tool calls:  
        - Use `write_file(path, content)` for persisting results  
        - For directory/file checks, use read/list tools  
        Do NOT hallucinate file operations.

        ### 4. Observation

        Briefly document the results of your most recent action(s), including confirmations of file saves or feedback interactions.

        ### 5. Final

        Deliver a polished, user-ready prompt as output and confirm all requirements are met prior to termination.

        ---

        ## Task Objective

        Generate engaging, professional, and on-brand social media posts for Network X (e.g., Twitter: https://twitter.com/en/tips#posting), based on a user-supplied topic or theme. Optimize every post for audience interaction, clarity, and adherence to platform best practices.

        ---

        ## Input Instructions

        - The user will provide a topic, keyword, or brief description.
        - If the input is unclear or too broad, request clarification before proceeding.

        ---

        ## Content Creation Guidelines

        - **Length:** Comply strictly with X's character limit (typically 280 characters).
        - **Relevance:** Align closely with the provided topic or theme.
        - **Clarity:** Avoid unnecessary jargon unless targeted at a technical audience.
        - **Engagement:** Incorporate calls to action, questions, or interesting facts where appropriate.
        - **Hashtags & Mentions:** Suggest 1-3 relevant/trending hashtags; include mentions if contextually justified.
        - **Originality:** Ensure all posts are unique; avoid copying existing online content.
        - **Variety:** If multiple posts are needed, each post should offer a fresh angle or distinct language.

        ---

        ## Output Format

        - Number posts if more than one is generated.
        - Present each post as a bullet point or within quotation marks.
        - List suggested hashtags separately at the end if not embedded.
        - Use markdown formatting for clarity.

        ---

        ## Tone and Style Recommendations

        - Maintain a professional, engaging, and current tone.
        - Reflect contemporary trends for Network X.
        - Remain mindful of cultural sensitivities; avoid divisive or offensive content.

        ---

        ## Agentic Reminders

        - Always reason via the Thought, Plan, Action, and Observation sections.
        - Only use tool calls to manipulate files or directories.
        - Do not end your session until a fully refined publication is produced, saved, and confirmed by the user.
    """
        ),
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

    def get_planened_publication(self, topic: str) -> Optional[str]:
        planned_publication = Memory.get_planened_publication(topic)
        return planned_publication

    def add_planened_publication(self, topic: str) -> Optional[str]:
        add_planened_publication = Memory.add_planened_publication(topic)
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

    def run(self, topic: str, use_cache: bool = True) -> Iterator[RunResponse]:
        logger.debug(f"Generating publication on: {topic} (Session Cache: {use_cache})")
        generate_publication_content = Optional[str] = None
        evalution_publication_content = Optional[str] = None
        improve_publication_content = Optional[str] = None

        logger.debug(f"Getting initial publications from cache {topic}")
        chaded_initial_publication = self.get_cached_initial_publication(topic)

        # --- Phase 1: Plan the content to generate --- #
        plan: Iterator[RunResponse] = self.orchestrator.run(
            topic, stream=True, markdown=True
        )
        logger.debug(f"Getting initial publications from cache {topic}")
        chaded_initial_publication = (

            self.get_cached_initial_publication(topic) if use_cache else None
        )
        if cached_initial_publication:
            logger.debug(f"Using cached initial publication: {cached_initial_publication}")
            generate_publication_content = cached_initial_publication
            yield RunResponse(content=f"# Initial Publication (cached) \n\n {generate_publication_content}"), event = RunEvent.run_response)
        else: 
            logger.info("Generating plan for publication")
            orchestrator_input = {
                "topic": topic,
                "task": "Create a plan for a team thats creates content for X based on this topic",
                "requirements": {
                    "format": "markdown",
                    "structure": "cluear sections",
                    "style": "eganging",
                }
            }
            try:
                plan: Optional[RunReponse] = (self.orchestrator.run(json.dumps(orchestrator_input, ident=4), stream=True)
                if not plan or not plan.content:
                    raise ValueError("Agent (Phase 1) did not return content.")
                plan_contetn = plan.content
                self.add_initial_publication_to_cache(topic, plan_content)
                yield RunResponse(content=f"# Plan for Publication (cached) \n\n {plan_content}"), event = RunEvent.run_response)
            except Exception as e:
                logger.error(f"Error during plan generation: {e}")
                yield RunResponse(
                    content=f"Error: Failed to generate the plan.\nDetails: {e}",
                    event=RunEvent.run_error,
                )
                return

