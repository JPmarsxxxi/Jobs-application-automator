"""
Vision Coordinator
Coordinates Llava (vision) + Llama (decision) for intelligent web automation
"""

import logging
import base64
import io
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
from PIL import Image

from modules.generation.ollama_client import get_ollama_client


class VisionCoordinator:
    """
    Coordinates vision-based web automation:
    1. Llava analyzes screenshot (brief description)
    2. Llama decides action (using vision + DOM context)
    """

    def __init__(self, vision_model: str = "llava:13b", decision_model: str = "llama3.1:8b"):
        self.vision_model = vision_model
        self.decision_model = decision_model
        self.ollama = get_ollama_client()
        self.logger = logging.getLogger(__name__)

        # Screenshots directory
        self.screenshot_dir = Path("workspace/screenshots/vision")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.action_count = 0

    def get_brief_visual_description(self, screenshot_path: str, goal: str, current_url: str) -> Optional[str]:
        """
        Use Llava to get a BRIEF description of the page (2-3 sentences).

        Args:
            screenshot_path: Path to screenshot
            goal: User's goal
            current_url: Current page URL

        Returns:
            Brief description from Llava
        """
        try:
            self.logger.info(f"🔮 LLAVA: Analyzing screenshot: {screenshot_path}")

            # Prompt for BRIEF description
            prompt = f"""Analyze this webpage screenshot and describe what you see in 2-3 SHORT sentences.

GOAL: {goal}
CURRENT URL: {current_url}

Be brief and focus on:
1. What type of page is this? (homepage, search results, product page, form, etc.)
2. What key interactive elements are visible? (search boxes, buttons, product listings, forms, etc.)
3. What's the main content/purpose?

Keep it under 100 words. Be specific but concise.

Description:"""

            # Use Ollama client's analyze_image method
            response = self.ollama.analyze_image(
                image_path=screenshot_path,
                prompt=prompt,
                model=self.vision_model
            )

            if response:
                # Truncate if too long
                if len(response) > 500:
                    response = response[:500] + "..."
                self.logger.info(f"✅ LLAVA: {response[:150]}...")
                return response
            else:
                self.logger.warning("❌ LLAVA: Returned empty response")
                return None

        except Exception as e:
            self.logger.error(f"❌ LLAVA ERROR: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def decide_action(
        self,
        visual_description: str,
        dom_elements: List[Dict],
        goal: str,
        current_url: str,
        history: List[Dict] = None,
        failed_patterns: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Use Llama to decide action based on visual description + DOM elements.

        Args:
            visual_description: Brief description from Llava
            dom_elements: List of interactive elements from DOM
            goal: User's goal
            current_url: Current URL
            history: Action history
            failed_patterns: Previously failed actions to avoid

        Returns:
            Action dict to execute
        """
        self.logger.info(f"🧠 LLAMA: Deciding action based on vision + {len(dom_elements)} DOM elements...")

        # Build recent history summary
        history_summary = []
        if history:
            for h in history[-5:]:  # Last 5 actions
                action = h.get('action', {})
                result = h.get('result', {})
                history_summary.append({
                    'action': action.get('action'),
                    'success': result.get('success', False),
                    'url': h.get('url', '')
                })

        # Build failed patterns summary
        avoid_patterns = []
        if failed_patterns:
            for pattern in failed_patterns[-5:]:  # Last 5 failures
                avoid_patterns.append({
                    'action': pattern.get('action'),
                    'selector': pattern.get('selector'),
                    'reason': pattern.get('reason')
                })

        # Format DOM elements (limit to 30 most relevant)
        elements_summary = []
        for i, elem in enumerate(dom_elements[:30]):
            elements_summary.append({
                'index': i,
                'type': elem.get('type'),
                'text': elem.get('text', '')[:80],  # Truncate long text
                'selector': elem.get('selector', '')
            })

        # System prompt
        system_prompt = """You are a web automation decision maker.
You receive:
1. A BRIEF visual description of the page from Llava (vision model)
2. Interactive DOM elements with selectors
3. User's goal

Decide ONE action to take next.

Available actions:
- navigate: {"action": "navigate", "url": "https://..."}
- click: {"action": "click", "selector": "CSS selector"}
- type: {"action": "type", "selector": "input selector", "text": "text to type"}
- select: {"action": "select", "selector": "select element", "value": "option"}
- press_key: {"action": "press_key", "key": "Enter|Tab|Escape"}
- scroll: {"action": "scroll", "direction": "down|up", "amount": 500}
- wait: {"action": "wait", "ms": 2000}
- extract_text: {"action": "extract_text", "selector": "element selector"}
- complete: {"action": "complete", "reason": "Goal achieved"}

IMPORTANT RULES:
1. Use selectors from DOM elements list (they are guaranteed to exist)
2. When typing in search box, it auto-submits with Enter
3. Prefer elements with meaningful text (avoid nav chrome like "nav-logo")
4. Check visual description for page type before acting
5. Match actions to page type (search on homepage, click products on results, etc.)

Return ONLY a JSON object with the action, no additional text."""

        # User prompt combining vision + DOM
        user_prompt = f"""GOAL: {goal}
CURRENT URL: {current_url}

VISUAL CONTEXT (from Llava):
{visual_description}

INTERACTIVE DOM ELEMENTS (with selectors):
{self._format_elements_for_prompt(elements_summary)}

RECENT HISTORY (last 5 actions):
{self._format_history_for_prompt(history_summary)}

{f'AVOID THESE PATTERNS (failed recently):\n{self._format_failed_patterns(avoid_patterns)}\n' if avoid_patterns else ''}

Based on the visual description and available DOM elements, what is the NEXT action?
Return ONLY the JSON action object."""

        # Call Llama
        try:
            # Use Ollama client's chat method
            response = self.ollama.chat(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.decision_model,
                temperature=0.2
            )

            if response:
                # Parse JSON from response
                import re
                import json
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    action = json.loads(json_match.group())

                    # Validate action has 'action' key
                    if 'action' not in action:
                        if 'type' in action:
                            action['action'] = action.pop('type')
                        else:
                            self.logger.warning("❌ LLAMA: Action missing 'action' key, using wait")
                            return {"action": "wait", "ms": 1000}

                    action_str = f"{action.get('action')} on {action.get('selector', action.get('element_description', 'unknown'))}"
                    self.logger.info(f"✅ LLAMA: Decided → {action_str}")
                    return action
                else:
                    self.logger.warning(f"❌ LLAMA: Could not parse JSON from response: {response[:200]}")
                    return {"action": "wait", "ms": 1000}
            else:
                self.logger.warning("❌ LLAMA: Returned empty response")
                return {"action": "wait", "ms": 1000}

        except Exception as e:
            self.logger.error(f"❌ LLAMA ERROR: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {"action": "wait", "ms": 1000}

    def _format_elements_for_prompt(self, elements: List[Dict]) -> str:
        """Format DOM elements for Llama prompt."""
        if not elements:
            return "No interactive elements found"

        formatted = []
        for elem in elements:
            elem_type = elem.get('type', 'unknown')
            elem_text = elem.get('text', '')[:60]
            selector = elem.get('selector', '')

            formatted.append(f"  [{elem_type}] {elem_text} → {selector}")

        return "\n".join(formatted[:25])  # Limit to 25 to avoid token overflow

    def _format_history_for_prompt(self, history: List[Dict]) -> str:
        """Format history for Llama prompt."""
        if not history:
            return "No previous actions"

        formatted = []
        for i, h in enumerate(history, 1):
            action = h.get('action', 'unknown')
            success = "✓" if h.get('success') else "✗"
            formatted.append(f"  {i}. {success} {action}")

        return "\n".join(formatted)

    def _format_failed_patterns(self, patterns: List[Dict]) -> str:
        """Format failed patterns for Llama prompt."""
        if not patterns:
            return ""

        formatted = []
        for p in patterns:
            action = p.get('action', 'unknown')
            selector = p.get('selector', '')
            reason = p.get('reason', '')
            formatted.append(f"  - {action} on {selector}: {reason}")

        return "\n".join(formatted)


def get_vision_coordinator() -> VisionCoordinator:
    """Get VisionCoordinator instance."""
    return VisionCoordinator()
