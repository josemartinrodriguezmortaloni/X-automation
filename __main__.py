from src.agents.agents import PublicationWorkflow
from agno.utils.pprint import pprint_run_response
from src.utils.knowledge import Knowledge
import logging
from src.utils.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


def main():
    # Load and index documents into the knowledge base (creates ChromaDB collection)
    try:
        Knowledge.knowledge_base.load(recreate=False)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Knowledge base load warning: {e}")

    # Instead of prompting in console, load the instructions file for Orchestrator
    detalles_publicacion = PromptLoader.load("instrucciones")

    # Initialize and run workflow using the file content
    generate_publications = PublicationWorkflow(
        session_id="generate-publication-session"
    )
    for phase_response in generate_publications.run(topic=detalles_publicacion):
        pprint_run_response(phase_response, markdown=True)
    # End of process


if __name__ == "__main__":
    main()
