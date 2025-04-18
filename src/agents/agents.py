from textwrap import dedent
from typing import Iterator
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.utils.log import logger
from agno.workflow import RunEvent, RunResponse, Workflow
from dotenv import load_dotenv
from ..utils.memory import Memory
from ..utils.tools import FileSystemTools

load_dotenv()


class PublicationWorkflow(Workflow):
    """Workflow for generating publications and chatting through dms for x using ia"""

    orchestrator: Agent = Agent(
        model=OpenAIResponses(id="o3"),
        instructions=dedent("""\
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


    """),
        reasoning=True,
        tools=[FileSystemTools()],
        markdown=True,
        show_tool_calls=True,
    )

    publication_writer: Agent = Agent(
        model=OpenAIResponses(id="gpt-4.1"),
        instructions=dedent("""\
                    
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

    """),
        markdown=True,
        show_tool_calls=True,
    )
    publication_evaluator: Agent = Agent(
        model=OpenAIResponses(id="o4-mini"),
        instructions=dedent("""\


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
    """),
        markdown=True,
        show_tool_calls=True,
    )
    publication_publisher: Agent = Agent(
        model=OpenAIResponses(id="gpt-4o"),
        instructions=dedent("""\

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
    """),
        markdown=True,
        show_tool_calls=True,
    )

    def __init__(
        self, session_id: str | None = None, debug_mode: bool = False, **kwargs
    ):
        # Llama al constructor de Workflow (que espera session_id, debug_mode, etc.)
        super().__init__(session_id=session_id, debug_mode=debug_mode, **kwargs)

        # Tu inicialización propia
        self.memory: Memory = Memory(session_id=session_id)

    # ---------------- Memory convenience wrappers ---------------- #

    # Initial prompts
    def cache_initial_prompt(self, topic: str, prompt: str):
        self.memory.add_initial_prompt_to_cache(topic, prompt)

    def get_initial_prompt(self, topic: str):
        return self.memory.get_cached_initial_prompt(topic)

    # Drafts & revisions
    def cache_draft(self, topic: str, draft: str):
        self.memory.add_draft_to_cache(topic, draft)

    def cache_revision(self, topic: str, content: str, iteration: int):
        self.memory.add_revision_to_cache(topic, content, iteration)

    def get_revision_history(self, topic: str):
        return self.memory.get_revision_history(topic)

    # Evaluations
    def cache_evaluation(self, topic: str, evaluation: str):
        self.memory.add_evaluation_to_cache(topic, evaluation)

    def get_cached_evaluation(self, topic: str):
        return self.memory.get_cached_evaluation(topic)

    # Approvals & final publications
    def mark_approved(self, topic: str):
        self.memory.mark_topic_as_approved(topic)

    def is_approved(self, topic: str) -> bool:
        return self.memory.is_topic_approved(topic)

    def save_final_publication(self, topic: str, publication: str):
        self.memory.save_final_publication(topic, publication)

    # Status log
    def log_status(self, agent: str, stage: str):
        self.memory.log_status(agent, stage)

    def get_status_log(self):
        return self.memory.get_status_log()

    def run(self, topic: str, use_cache: bool = True) -> Iterator[RunResponse]:
        logger.info(f"Run({topic})")
        iteration = 0

        # 1) Draft ----------------------------------------------------------------
        draft = self.get_initial_prompt(topic) if use_cache else None
        if not draft:
            self.log_status("Writer", "draft_requested")
            draft_resp = self.publication_writer.run(topic, stream=False)
            draft = draft_resp.content
            self.cache_draft(topic, draft)
            yield RunResponse(content=f"Draft:\n\n{draft}", event=RunEvent.run_response)
        else:
            yield RunResponse(content="Draft (cached) ", event=RunEvent.run_response)

        # 2‑3) Loop: evaluate -> maybe revise -------------------------------------
        approved = self.is_approved(topic)
        while not approved:
            # --- evaluación
            evaluation = (
                self.get_cached_evaluation(topic)
                if use_cache and iteration == 0
                else None
            )
            if not evaluation:
                self.log_status("Evaluator", "evaluation_requested")
                eval_resp = self.publication_evaluator.run(draft, stream=False)
                evaluation = eval_resp.content
                self.cache_evaluation(topic, evaluation)
            yield RunResponse(
                content=f"Evaluation:\n\n{evaluation}", event=RunEvent.run_response
            )

            # ¿aprobado?
            if "Publish" in evaluation:  # o parsear tu «Decision: Publish»
                self.mark_approved(topic)
                approved = True
                break

            # --- no aprobado: pedir revisión
            iteration += 1
            self.log_status("Writer", f"revision_{iteration}_requested")
            rev_prompt = f"{draft}\n\n### Feedback\n{evaluation}"
            rev_resp = self.publication_writer.run(rev_prompt, stream=False)
            draft = rev_resp.content
            self.cache_revision(topic, draft, iteration)
            yield RunResponse(
                content=f"Revision {iteration}:\n\n{draft}", event=RunEvent.run_response
            )

        # 4) Publicación -----------------------------------------------------------
        self.log_status("Publisher", "publish_requested")
        pub_resp = self.publication_publisher.run(draft, stream=False)
        published_content = pub_resp.content
        yield RunResponse(
            content=f"Published:\n\n{published_content}", event=RunEvent.run_response
        )

        # 5) Evaluación post‑publicación ------------------------------------------
        self.log_status("Evaluator", "post_publish_evaluation_requested")
        post_eval_resp = self.publication_evaluator.run(published_content, stream=False)
        post_evaluation = post_eval_resp.content
        yield RunResponse(
            content=f"Post‑publish Evaluation:\n\n{post_evaluation}",
            event=RunEvent.run_response,
        )

        # Guardar solo si la evaluación final es positiva
        if "Publish" in post_evaluation:
            self.save_final_publication(topic, published_content)
            self.log_status("Orchestrator", "publication_saved")
        else:
            self.log_status("Orchestrator", "post_publish_evaluation_failed")
