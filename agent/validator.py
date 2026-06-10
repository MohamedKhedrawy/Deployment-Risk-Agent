"""Input Validator — checks if a feature description is a valid software deployment request."""

from google.genai import types
from agent.llm_client import llm_client

class InputValidator:
    def __init__(self):
        pass

    async def check(self, feature_description: str) -> tuple[bool, str]:
        """Check if the input is a valid feature description.

        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        cleaned = feature_description.strip()

        # --- 1. Preliminary Heuristic Checks ---
        if len(cleaned) < 10:
            return False, "Please provide a more detailed feature description (minimum 10 characters)."

        words = cleaned.split()
        if len(words) < 3:
            return False, "Your description is too short. Please describe the specific software change in a few words."

        # Simple check for repeated nonsense characters (e.g. 'aaaaaa')
        if len(set(cleaned.replace(" ", ""))) < 4:
            return False, "The input appears to be random characters. Please provide a meaningful description."

        # Regex check: ensure it has at least some consecutive alphabetical letters
        import re
        if not re.search(r'[a-zA-Z]{3,}', cleaned):
            return False, "Please use real words to describe the feature or deployment request."

        # If no API key is provided, heuristics pass is enough
        if not llm_client.is_configured():
            return True, ""

        # --- 2. LLM Correctness Check ---

        prompt = (
            "You are an expert software engineering manager evaluating a deployment request.\n"
            "Your task is to determine if the input genuinely describes a meaningful software feature, "
            "bug fix, configuration change, or system deployment.\n\n"
            "REJECT the input if it is:\n"
            "- A test string, keyboard mashing (e.g. 'asas dsds', 'test', '1234').\n"
            "- Too vague or completely lacks technical/product context.\n"
            "- A joke, spam, or a request unrelated to software engineering.\n\n"
            "ACCEPT the input only if it sounds like a real change that a developer or ops engineer would make.\n\n"
            "If accepting, output exactly: VALID\n"
            "If rejecting, output exactly: INVALID|Your friendly reason here\n\n"
            "Example rejection:\n"
            "INVALID|Please provide more details about the technical changes being made.\n\n"
            f"Input:\n{feature_description}"
        )

        try:
            # Note: We run this synchronously; since it's a fast model it shouldn't block long.
            response = llm_client.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=60,
                )
            )
            text = response.text.strip() if response.text else ""

            if text.upper().startswith("INVALID"):
                parts = text.split("|", 1)
                reason = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Please provide a more detailed and meaningful feature description."
                return False, reason

            return True, ""

        except Exception as e:
            # If the LLM call fails, fail closed for auth errors but fail-open for rate limits
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg or "API_KEY" in error_msg:
                return False, "Validation failed: Authentication to Vertex AI failed. Please verify your Google Cloud ADC and project configuration."
            if "429" in error_msg or "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                # Rate limit — heuristics already passed, let it through
                return True, ""
            return False, f"LLM Validation failed due to API error: {error_msg}"
