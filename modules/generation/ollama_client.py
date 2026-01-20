"""
Ollama Client

Provides interface to local Ollama server for LLM inference.
Supports both text generation (Llama) and vision models (LLaVA).
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
import base64

from modules.core.logger import get_logger


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        text_model: str = "llama3.1:8b",
        vision_model: str = "llava:13b",
        timeout: int = 300,
    ):
        """
        Initialize Ollama client

        Args:
            host: Ollama server host
            text_model: Model name for text generation
            vision_model: Model name for vision tasks
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip("/")
        self.text_model = text_model
        self.vision_model = vision_model
        self.timeout = timeout
        self.logger = get_logger()

    def check_connection(self) -> bool:
        """
        Check if Ollama server is accessible

        Returns:
            True if connected, False otherwise
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("✓ Connected to Ollama server")
                return True
            else:
                self.logger.error(f"Ollama server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.logger.error(
                f"Could not connect to Ollama at {self.host}. "
                "Make sure Ollama is running: `ollama serve`"
            )
            return False
        except Exception as e:
            self.logger.error(f"Error connecting to Ollama: {e}")
            return False

    def list_models(self) -> List[str]:
        """
        List available models

        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
            return []
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []

    def check_models(self) -> bool:
        """
        Check if required models are available

        Returns:
            True if all required models are available
        """
        models = self.list_models()
        if not models:
            self.logger.error("No models found. Please install required models:")
            self.logger.error(f"  ollama pull {self.text_model}")
            self.logger.error(f"  ollama pull {self.vision_model}")
            return False

        missing_models = []
        if self.text_model not in models:
            missing_models.append(self.text_model)
        if self.vision_model not in models:
            missing_models.append(self.vision_model)

        if missing_models:
            self.logger.error(f"Missing models: {', '.join(missing_models)}")
            for model in missing_models:
                self.logger.error(f"  Install with: ollama pull {model}")
            return False

        self.logger.info(f"✓ Required models available: {self.text_model}, {self.vision_model}")
        return True

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Chat-style text generation (alias for generate_text for compatibility).

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (default: self.text_model)

        Returns:
            Generated text or None if error
        """
        return self.generate_text(prompt, system_prompt, temperature, max_tokens, model)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate text using text model

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (default: self.text_model)

        Returns:
            Generated text or None if error
        """
        model = model or self.text_model

        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if system_prompt:
                payload["system"] = system_prompt

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            self.logger.debug(f"Generating text with model: {model}")

            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("response", "")
                self.logger.debug(f"Generated {len(generated_text)} characters")
                return generated_text
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            self.logger.error(f"Ollama request timed out after {self.timeout}s")
            return None
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return None

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Analyze an image using vision model

        Args:
            image_path: Path to image file
            prompt: Prompt describing what to analyze
            model: Vision model to use (default: self.vision_model)

        Returns:
            Analysis result or None if error
        """
        model = model or self.vision_model

        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "model": model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
            }

            self.logger.debug(f"Analyzing image with model: {model}")

            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                analysis = data.get("response", "")
                self.logger.debug(f"Image analysis complete ({len(analysis)} chars)")
                return analysis
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None

        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            return None
        except requests.exceptions.Timeout:
            self.logger.error(f"Ollama request timed out after {self.timeout}s")
            return None
        except Exception as e:
            self.logger.error(f"Error analyzing image: {e}")
            return None

    def generate_with_prompt_file(
        self,
        prompt_file: str,
        variables: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Generate text using a prompt template file

        Args:
            prompt_file: Path to prompt file
            variables: Variables to substitute in prompt
            **kwargs: Additional arguments for generate_text()

        Returns:
            Generated text or None if error
        """
        try:
            # Read prompt file
            prompt_path = Path(prompt_file)
            if not prompt_path.exists():
                self.logger.error(f"Prompt file not found: {prompt_file}")
                return None

            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()

            # Substitute variables
            if variables:
                for key, value in variables.items():
                    placeholder = f"{{{{{key}}}}}"
                    prompt_template = prompt_template.replace(placeholder, str(value))

            # Generate text
            return self.generate_text(prompt_template, **kwargs)

        except Exception as e:
            self.logger.error(f"Error processing prompt file: {e}")
            return None

    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from LLM response

        Sometimes LLMs wrap JSON in markdown or add extra text.
        This method tries to extract the JSON portion.

        Args:
            text: Text containing JSON

        Returns:
            Parsed JSON or None if not found
        """
        try:
            # Try direct parsing first
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        import re

        patterns = [
            r"```json\s*(\{.*?\})\s*```",  # JSON in code block
            r"```\s*(\{.*?\})\s*```",  # Code block without language
            r"(\{.*\})",  # Raw JSON
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        self.logger.warning("Could not extract JSON from LLM response")
        return None


# Singleton instance
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client singleton"""
    global _ollama_client
    if _ollama_client is None:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        text_model = os.getenv("OLLAMA_TEXT_MODEL", "llama3.1:8b")
        vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava:13b")
        timeout = int(os.getenv("OLLAMA_TIMEOUT", "300"))

        _ollama_client = OllamaClient(
            host=host,
            text_model=text_model,
            vision_model=vision_model,
            timeout=timeout,
        )

    return _ollama_client
