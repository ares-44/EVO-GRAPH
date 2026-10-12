
import json
import os
import urllib.request
import urllib.error


class LLMAdapter:
    """Local LLM adapter for EVO-GRAPH using Ollama."""

    def __init__(
        self,
        provider=None,
        ollama_model=None,
        ollama_url=None,
    ):
        self.provider = (
            provider or os.getenv("EVO_LLM_PROVIDER", "ollama")
        ).lower()

        self.ollama_model = (
            ollama_model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        )

        self.ollama_url = (
            ollama_url
            or os.getenv(
                "OLLAMA_URL",
                "http://localhost:11434/api/generate",
            )
        )

        if self.provider != "ollama":
            raise ValueError("Only Ollama is supported.")

    def generate(self, prompt):
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
        }

        request = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))

            answer = result.get("response", "").strip()
            if not answer:
                raise RuntimeError("Ollama returned an empty response.")

            return answer

        except urllib.error.HTTPError as error:
            raise RuntimeError(
                f"Ollama HTTP error: {error.code}. Check the model."
            ) from error

        except urllib.error.URLError as error:
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it is running."
            ) from error


if __name__ == "__main__":
    llm = LLMAdapter()
    print(llm.generate("Explain Python debugging in 3 short points."))
