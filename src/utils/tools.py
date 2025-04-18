import os
import difflib
from rich.syntax import Syntax
from rich.console import Console
from rich.panel import Panel
from agno.tools import Toolkit
from agno.utils.log import logger

console = Console()


class FileSystemTools(Toolkit):
    def __init__(self):
        super().__init__(name="file_system_tools")
        # Registrar las funciones que serán herramientas para el agente
        self.register(self.create_folder)
        self.register(self.create_file)
        self.register(self.edit_and_apply)
        self.register(self.read_file)
        self.register(self.list_files)
        # No registramos _highlight_diff ni _generate_and_apply_diff
        # ya que son helpers internos para edit_and_apply

    def create_folder(self, path: str) -> str:
        """Creates a directory at the specified path, including parent directories.

        Args:
            path (str): The path where the folder should be created.

        Returns:
            str: Confirmation message or error message.
        """
        logger.info(f"Attempting to create folder: {path}")
        try:
            os.makedirs(path, exist_ok=True)
            return f"Folder created successfully: {path}"
        except Exception as e:
            logger.error(f"Error creating folder {path}: {e}")
            return f"Error creating folder: {str(e)}"

    def create_file(self, path: str, content: str = "") -> str:
        """Creates a file at the specified path with optional content. Overwrites if exists.

        Args:
            path (str): The path where the file should be created.
            content (str, optional): The initial content of the file. Defaults to "".

        Returns:
            str: Confirmation message or error message.
        """
        logger.info(f"Attempting to create file: {path}")
        try:
            # Ensure the directory exists before writing the file
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File created successfully: {path}"
        except Exception as e:
            logger.error(f"Error creating file {path}: {e}")
            return f"Error creating file: {str(e)}"

    def _highlight_diff(self, diff_text: str):
        """Internal helper to highlight diff text using rich.syntax."""
        # Note: This returns a rich object, not directly useful as tool output
        try:
            return Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        except Exception as e:
            logger.warning(f"Could not highlight diff: {e}")
            return diff_text  # Return plain text if highlighting fails

    def _generate_and_apply_diff(
        self, original_content: str, new_content: str, path: str
    ) -> str:
        """Internal helper to generate diff, apply changes, and return summary."""
        diff = list(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                n=3,
            )
        )

        if not diff:
            return "No changes detected."

        try:
            # Apply the changes by writing the new content
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(new_content)

            # --- Optional: Console Output (for debugging/user feedback) ---
            diff_text = "".join(diff)
            highlighted_diff = self._highlight_diff(diff_text)
            diff_panel = Panel(
                highlighted_diff,
                title=f"Changes applied to {path}",
                expand=False,
                border_style="cyan",
            )
            console.print(diff_panel)
            # --- End Optional Console Output ---

            added_lines = sum(
                1
                for line in diff
                if line.startswith("+") and not line.startswith("+++")
            )
            removed_lines = sum(
                1
                for line in diff
                if line.startswith("-") and not line.startswith("---")
            )

            summary = f"Changes successfully applied to {path}:\n"
            summary += f"  Lines added: {added_lines}\n"
            summary += f"  Lines removed: {removed_lines}"
            return summary

        except Exception as e:
            logger.error(f"Error applying changes to {path}: {e}")
            # --- Optional: Console Output ---
            error_panel = Panel(
                f"Error: {str(e)}", title="Error Applying Changes", style="bold red"
            )
            console.print(error_panel)
            # --- End Optional Console Output ---
            return f"Error applying changes to file {path}: {str(e)}"

    def edit_and_apply(self, path: str, new_content: str) -> str:
        """Reads a file, compares with new content, and applies changes if different.

        Args:
            path (str): The path of the file to edit.
            new_content (str): The proposed new content for the file.

        Returns:
            str: A summary of the changes applied, 'No changes needed', or an error message.
        """
        logger.info(f"Attempting to edit file: {path}")
        try:
            if not os.path.exists(path):
                return f"Error: File not found at {path}. Use create_file first."
            with open(path, "r", encoding="utf-8") as file:
                original_content = file.read()

            if new_content != original_content:
                # Call the internal helper method using self
                diff_result = self._generate_and_apply_diff(
                    original_content, new_content, path
                )
                return diff_result
            else:
                logger.info(f"No changes needed for {path}")
                return f"No changes needed for {path}"
        except Exception as e:
            logger.error(f"Error reading or comparing file {path}: {e}")
            return f"Error editing file {path}: {str(e)}"

    def read_file(self, path: str) -> str:
        """Reads the content of a file.

        Args:
            path (str): The path of the file to read.

        Returns:
            str: The content of the file, or an error message if reading fails.
        """
        logger.info(f"Attempting to read file: {path}")
        try:
            if not os.path.exists(path):
                return f"Error: File not found at {path}."
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Return only a portion if it's too large? For now, return all.
            # Consider adding size limits if needed.
            return content
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return f"Error reading file: {str(e)}"

    def list_files(self, path: str = ".") -> str:
        """Lists files and directories in the specified path.

        Args:
            path (str, optional): The directory path to list. Defaults to ".".

        Returns:
            str: A newline-separated list of file/directory names, or an error message.
        """
        logger.info(f"Attempting to list files in: {path}")
        try:
            if not os.path.isdir(path):
                return f"Error: Path is not a valid directory: {path}"
            files = os.listdir(path)
            return "\n".join(files) if files else "Directory is empty."
        except Exception as e:
            logger.error(f"Error listing files in {path}: {e}")
            return f"Error listing files: {str(e)}"
