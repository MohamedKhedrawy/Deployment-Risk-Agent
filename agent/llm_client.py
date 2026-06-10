import os
import logging
from google import genai

logger = logging.getLogger(__name__)

class VertexLLMClient:
    def __init__(self):
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        if not self.project:
            logger.warning("GOOGLE_CLOUD_PROJECT not set for Vertex AI!")

    def is_configured(self):
        return bool(self.project)

    def get_client(self):
        return genai.Client(vertexai=True, project=self.project, location=self.location)

    def rotate_key(self):
        pass # No keys to rotate in Vertex AI

    def generate_content(self, model: str, contents: str, config=None, max_retries: int = None):
        if not self.is_configured():
            raise ValueError("Vertex AI project not configured.")

        if max_retries is None:
            max_retries = 3

        attempts = 0
        last_error = None

        while attempts < max_retries:
            client = self.get_client()
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"Rate limit hit in Vertex AI. (Attempt {attempts + 1})")
                else:
                    raise
                attempts += 1

        raise Exception(f"Failed to generate content after {attempts} attempts. Last error: {last_error}")

# Global instance
llm_client = VertexLLMClient()
