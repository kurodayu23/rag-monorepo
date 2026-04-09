import re
from pathlib import Path

from .ollama_client import OllamaClient


class QtAnnotatorSkill:
    """
    Skill: annotate a C++/Qt source file with Doxygen-style block comments.

    Goal for the portfolio: show a “skill” that takes structured input (a file path)
    and returns modified code text, without depending on cloud APIs.
    """

    SYSTEM_PROMPT = """
You are a C++/Qt code documentation assistant.
Analyze the provided C++/Qt source code and add Doxygen-style block comments.

Output requirements:
1) Return ONLY the updated C++ code (no markdown wrapper).
2) Add comments for:
   - signals/slots intent
   - pointer ownership / QObject tree expectations
   - macro usage and namespace boundaries
"""

    def __init__(self, model_name: str = "gemma2:9b"):
        self.client = OllamaClient(model=model_name)

    def execute(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found at {file_path}")

        code_content = path.read_text(encoding="utf-8")

        ai_response = self.client.prompt(
            system_prompt=self.SYSTEM_PROMPT.strip(),
            user_prompt=f"Please analyze and annotate this file:\n\n{code_content}",
        )

        # Best-effort cleanup if the model wraps code in fences.
        ai_response = re.sub(r"^\s*```(?:cpp)?\s*", "", ai_response)
        ai_response = re.sub(r"\s*```\s*$", "", ai_response)
        return ai_response.strip()

