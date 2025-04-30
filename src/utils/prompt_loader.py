from pathlib import Path
from string import Template


class PromptLoader:
    """
    Utility for loading and interpolating prompt templates from the agents/prompts directory.
    """

    @staticmethod
    def load(template_name: str, **kwargs) -> str:
        """Load a text template by name and substitute provided variables."""
        # Determine the prompts directory relative to this file
        base = Path(__file__).parent
        prompts_dir = base.parent / "agents" / "prompts"
        template_path = prompts_dir / f"{template_name}.md"
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        content = template_path.read_text(encoding="utf-8")
        return Template(content).safe_substitute(**kwargs)
