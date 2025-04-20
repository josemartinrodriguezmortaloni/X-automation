from src.agents.agents import PublicationWorkflow
from agno.utils.pprint import pprint_run_response
from typing import Iterator
from agno.workflow import RunResponse
import random
from rich.prompt import Prompt
import logging

logger = logging.getLogger(__name__)


def main():
    while True:
        # Fun example prompts to showcase the generator's versatility
        example_prompts = [
            "10 consejos para aumentar tu engagement en X sin usar hashtags",
            "Cómo convertí mi cuenta de X en una fuente de ingresos pasivos en solo 3 meses",
            "La estrategia de contenido en X que me llevó de 0 a 10K seguidores en 30 días",
            "Por qué el algoritmo de X favorece a quienes publican a estas horas específicas",
            "5 formatos de publicaciones en X que generan más retuits que cualquier otro contenido",
        ]

        # Get topic from user
        topic = Prompt.ask(
            "[bold]Enter a  topic[/bold] (or press Enter for a random example)\n✨",
            default=random.choice(example_prompts),
        )
        if topic.lower() == "exit":
            break
        else:
            # Convert the topic to a URL-safe string for use in session_id
            url_safe_topic = topic.lower().replace(" ", "-")

            # Initialize the prompt generator workflow
            generate_publications = PublicationWorkflow(
                session_id=f"generate-publication-on-{url_safe_topic}"
            )

            # Execute the workflow
            result: Iterator[RunResponse] = generate_publications.run(topic=topic)

            # Print the response for each phase separately
            for phase_response in result:
                pprint_run_response(phase_response, markdown=True)


if __name__ == "__main__":
    main()
