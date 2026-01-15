#!/usr/bin/env python3
"""
Test Ollama Connection and Models

Run this to verify Ollama is installed and configured correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.generation.ollama_client import get_ollama_client
from modules.core.logger import setup_logger, get_logger


def test_connection():
    """Test connection to Ollama server"""
    logger = get_logger()
    logger.info("Testing Ollama connection...")

    client = get_ollama_client()

    if not client.check_connection():
        logger.error("❌ Ollama connection failed")
        logger.error("\nMake sure Ollama is running:")
        logger.error("  ollama serve")
        return False

    logger.info("✓ Ollama server is running")
    return True


def test_models():
    """Test if required models are available"""
    logger = get_logger()
    logger.info("\nChecking required models...")

    client = get_ollama_client()

    if not client.check_models():
        logger.error("❌ Required models not available")
        logger.error("\nInstall missing models:")
        logger.error("  ollama pull llama3.1:8b")
        logger.error("  ollama pull llava:13b")
        return False

    logger.info("✓ All required models are available")
    return True


def test_text_generation():
    """Test text generation"""
    logger = get_logger()
    logger.info("\nTesting text generation...")

    client = get_ollama_client()

    prompt = "Write a one-sentence professional greeting for a job application email."
    logger.info(f"Prompt: {prompt}")

    result = client.generate_text(prompt, temperature=0.7)

    if result:
        logger.info(f"✓ Text generation successful")
        logger.info(f"Response: {result[:200]}...")
        return True
    else:
        logger.error("❌ Text generation failed")
        return False


def main():
    """Run all tests"""
    setup_logger(level="INFO", log_to_console=True, log_to_file=False)
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("Ollama Connection Test")
    logger.info("=" * 60)

    results = []

    # Test 1: Connection
    results.append(test_connection())

    # Test 2: Models
    if results[-1]:  # Only if connection succeeded
        results.append(test_models())

    # Test 3: Text generation
    if results[-1]:  # Only if models check succeeded
        results.append(test_text_generation())

    # Summary
    logger.info("\n" + "=" * 60)
    if all(results):
        logger.info("✅ All tests passed! Ollama is ready to use.")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("❌ Some tests failed. Please fix the issues above.")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
