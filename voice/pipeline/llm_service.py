"""LLM service using OpenAI GPT-4o Realtime API."""

from typing import Callable, Optional, List, Dict
from loguru import logger
from openai import AsyncOpenAI

from config import settings


class LLMService:
    """Manages conversation with GPT-4o Realtime API."""

    def __init__(
        self,
        on_response: Callable[[str], None],
        on_function_call: Optional[Callable[[str, Dict], None]] = None
    ):
        """
        Initialize LLM service.

        Args:
            on_response: Callback function(response_text: str)
            on_function_call: Optional callback for function calls
        """
        self.on_response = on_response
        self.on_function_call = on_function_call
        self.client: Optional[AsyncOpenAI] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt: str = ""

    def connect(self):
        """Initialize OpenAI client."""
        try:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("✅ LLM: OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ LLM: Failed to initialize: {e}")
            raise

    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the conversation."""
        self.system_prompt = prompt
        logger.info(f"📝 LLM: System prompt set ({len(prompt)} chars)")

    def add_user_message(self, message: str):
        """Add user message to conversation history."""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        logger.debug(f"👤 User: {message}")

    def add_assistant_message(self, message: str):
        """Add assistant message to conversation history."""
        self.conversation_history.append({
            "role": "assistant",
            "content": message
        })

    async def generate_response(self, user_input: str) -> str:
        """
        Generate response to user input using streaming.

        Args:
            user_input: User's message

        Returns:
            Assistant's response
        """
        if not self.client:
            logger.error("❌ LLM: Client not initialized")
            return "I'm sorry, I'm having technical difficulties."

        try:
            # Add user message to history
            self.add_user_message(user_input)

            # Prepare messages
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.extend(self.conversation_history[-10:])  # Keep last 10 exchanges

            logger.debug(f"🤖 LLM: Generating response to: {user_input[:50]}...")

            # Stream response from GPT-4o
            response_text = ""
            stream = await self.client.chat.completions.create(
                model="gpt-4o",  # Using standard GPT-4o for now
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                stream=True,
            )

            # Process streaming response
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    # Optionally call on_response for each chunk
                    # self.on_response(content)

            # Add assistant response to history
            self.add_assistant_message(response_text)

            logger.debug(f"🤖 LLM: Response: {response_text[:100]}...")

            # Call response callback with complete response
            if self.on_response:
                self.on_response(response_text)

            return response_text

        except Exception as e:
            logger.error(f"❌ LLM: Error generating response: {e}")
            error_message = "I apologize, I'm having trouble processing that. Could you rephrase?"
            return error_message

    async def generate_response_streaming(self, user_input: str):
        """
        Generate response with word-by-word streaming.

        Args:
            user_input: User's message
        """
        if not self.client:
            logger.error("❌ LLM: Client not initialized")
            return

        try:
            self.add_user_message(user_input)

            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.extend(self.conversation_history[-10:])

            logger.debug(f"🤖 LLM: Streaming response to: {user_input[:50]}...")

            full_response = ""
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                stream=True,
            )

            # Stream each word/chunk as it arrives
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

                    # Call callback for each chunk (for real-time TTS)
                    if self.on_response:
                        self.on_response(content)

            self.add_assistant_message(full_response)
            logger.debug(f"✅ LLM: Streaming complete")

        except Exception as e:
            logger.error(f"❌ LLM: Streaming error: {e}")

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("🗑️  LLM: Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
