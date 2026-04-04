"""LLM service using OpenAI GPT-4o API with optional function-calling tools."""

import json
from typing import Callable, Optional, List, Dict, Awaitable, Union
from loguru import logger
from openai import AsyncOpenAI

from config import settings


class LLMService:
    """Manages conversation with GPT-4o, supporting optional tool/function calls."""

    def __init__(
        self,
        on_response: Callable[[str], None],
        on_function_call: Optional[Callable[[str, Dict], Awaitable[str]]] = None,
        tools: Optional[List[Dict]] = None,
    ):
        """
        Initialize LLM service.

        Args:
            on_response: Callback(response_text: str) — called with final text reply.
            on_function_call: Async callback(function_name: str, args: Dict) → str (JSON result).
                              Required when tools are provided.
            tools: OpenAI tool definitions (list of {"type": "function", ...} dicts).
        """
        self.on_response = on_response
        self.on_function_call = on_function_call
        self.tools = tools or []
        self.client: Optional[AsyncOpenAI] = None
        self.conversation_history: List[Dict] = []
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

    async def generate_response_with_tools(self, user_input: str) -> str:
        """
        Generate a response with tool/function-calling support.

        Flow:
          1. Call GPT-4o with the current tools list.
          2. If GPT-4o returns a tool_call, invoke on_function_call with the
             function name + args and feed the result back to GPT-4o.
          3. Repeat until GPT-4o returns a plain text response.
          4. Call on_response(text) with the final reply.

        Falls back to plain generate_response() if no tools are configured.
        """
        if not self.tools:
            return await self.generate_response(user_input)

        if not self.client:
            logger.error("❌ LLM: Client not initialized")
            return "I'm sorry, I'm having technical difficulties."

        self.add_user_message(user_input)

        # Build message list (system + last 10 turns)
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.conversation_history[-10:])

        MAX_TOOL_ROUNDS = 3  # safety cap to prevent infinite loops
        for _ in range(MAX_TOOL_ROUNDS):
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=400,
                )
            except Exception as e:
                logger.error(f"❌ LLM: API error: {e}")
                return "I apologize, I'm having trouble processing that."

            choice = response.choices[0]

            # ── Plain text response → done ────────────────────────────────
            if choice.finish_reason == "stop" or not choice.message.tool_calls:
                text = choice.message.content or ""
                self.add_assistant_message(text)
                if self.on_response:
                    self.on_response(text)
                logger.debug(f"🤖 LLM (tools): {text[:120]}")
                return text

            # ── Tool call(s) → execute each, feed results back ────────────
            assistant_msg = {
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                logger.info(f"🔧 LLM tool call: {fn_name}({fn_args})")

                if self.on_function_call:
                    try:
                        tool_result = await self.on_function_call(fn_name, fn_args)
                    except Exception as e:
                        logger.error(f"❌ Tool call execution failed ({fn_name}): {e}")
                        tool_result = json.dumps({"error": str(e)})
                else:
                    tool_result = json.dumps({"error": "No function call handler registered."})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # Fallback if loop exhausted
        logger.warning("⚠️  LLM: Tool call loop limit reached, returning safe fallback.")
        fallback = "I'm looking into that for you. Could you give me just a moment?"
        if self.on_response:
            self.on_response(fallback)
        return fallback

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("🗑️  LLM: Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
