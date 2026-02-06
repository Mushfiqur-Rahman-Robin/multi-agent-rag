"""
Chat service module for orchestrating multi-agent interactions.

Manages the lifecycle of a chat session, including database persistence,
agent graph execution, and streaming responses.
Integrated with Redis for response caching and context windowing for persistent memory.
"""

import hashlib
import json
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.multi_agent_rag.agents.graph import create_multi_agent_graph
from src.multi_agent_rag.core.config import (
    DEFAULT_MODEL,
    MAX_CONTEXT_CHARS,
    MAX_HISTORY_MESSAGES,
    OPENAI_API_KEY,
    USER_UPLOAD_DIR,
)
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.core.multimodal import create_multimodal_message
from src.multi_agent_rag.repositories.chat_repository import ChatRepository

# Import cache service
try:
    from src.multi_agent_rag.services.cache_service import cache_service
except ImportError:
    cache_service = None


class ChatService:
    """
    Service layer for managing chatbot interactions and orchestrating the multi-agent graph.
    """

    def __init__(self, repository: ChatRepository):
        self.repository = repository
        self.graph = create_multi_agent_graph()

    async def get_all_sessions(self):
        return await self.repository.get_conversations()

    async def get_session_history(self, thread_id: str):
        return await self.repository.get_messages(thread_id)

    async def delete_session(self, thread_id: str):
        await self.repository.delete_conversation(thread_id)

    def _get_request_hash(self, message: str, history: list, files: list[str]) -> str:
        """Generate a hash for the current request context."""
        context_str = (
            message + "".join([str(m.content) for m in history]) + "".join(files)
        )
        return hashlib.sha256(context_str.encode()).hexdigest()

    async def _generate_and_update_title(
        self, thread_id: str, first_message: str, model: str
    ):
        """Generate a descriptive title for the conversation."""
        try:
            llm = ChatOpenAI(
                model=model, openai_api_key=OPENAI_API_KEY, temperature=0.7
            )
            prompt = f"Generate a short title (max 5 words) for: '{first_message[:100]}'. Return ONLY the title."

            from langchain_community.callbacks import get_openai_callback

            from src.multi_agent_rag.services.cost_service import cost_service

            with get_openai_callback() as cb:
                response = await llm.ainvoke(prompt)
                title = response.content.strip().replace('"', "")[:50]
                actual_cost = cost_service.calculate_cost(
                    model, cb.prompt_tokens, cb.completion_tokens
                )

                await self.repository.update_conversation_title(thread_id, title)
                await self.repository.update_conversation_cost(thread_id, actual_cost)
        except Exception as e:
            logger.error(f"Title generation failed: {e}")

    def _build_context_history(self, db_messages: list) -> list:
        """Build context-aware message history with smart truncation."""
        history = []
        total_chars = 0

        # Filter for recent human/ai messages within limit
        messages_to_process = db_messages[-MAX_HISTORY_MESSAGES:]

        for m in messages_to_process:
            content_obj = (
                m.content
                if isinstance(m.content, dict)
                else (
                    json.loads(m.content)
                    if isinstance(m.content, str) and m.content.startswith("{")
                    else m.content
                )
            )

            if m.role == "human":
                msg_text = (
                    content_obj.get("message", str(content_obj))
                    if isinstance(content_obj, dict)
                    else str(content_obj)
                )
                history.append(HumanMessage(content=msg_text[:1000]))
                total_chars += len(msg_text[:1000])
            else:
                if isinstance(content_obj, dict):
                    parts = [content_obj.get("response", "")]
                    if content_obj.get("code"):
                        parts.append(f"\n[Code: {content_obj['code'][:200]}...]")
                    msg_text = " ".join(parts)[:1000]
                else:
                    msg_text = str(content_obj)[:1000]
                history.append(AIMessage(content=msg_text))
                total_chars += len(msg_text)

        while total_chars > MAX_CONTEXT_CHARS and len(history) > 2:
            removed = history.pop(0)
            total_chars -= len(removed.content)
            if history and isinstance(history[0], AIMessage):
                removed_ai = history.pop(0)
                total_chars -= len(removed_ai.content)
        return history

    async def run_chat_flow(
        self,
        message: str,
        thread_id: str | None,
        files: list[str],
        model: str | None = None,
    ):
        """Executes a chat interaction synchronously with caching."""
        # Ensure conversation exists
        if not thread_id:
            thread_id = str(uuid.uuid4())
            await self.repository.create_conversation(thread_id, "New Chat")
            await self._generate_and_update_title(
                thread_id, message, model or DEFAULT_MODEL
            )
        else:
            # Check if thread exists in DB (it might have been generated in the route)
            existing = await self.repository.get_conversation(thread_id)
            if not existing:
                await self.repository.create_conversation(thread_id, "New Chat")
                await self._generate_and_update_title(
                    thread_id, message, model or DEFAULT_MODEL
                )

        db_messages = await self.repository.get_messages(thread_id)
        history = self._build_context_history(db_messages)

        # Check Response Cache
        request_hash = self._get_request_hash(message, history, files)
        if cache_service and cache_service.is_available:
            cached_resp = await cache_service.get_response_cache(request_hash)
            if cached_resp:
                logger.info(f"Response cache HIT for thread {thread_id}")
                if files:
                    file_urls = [
                        f"/user_upload/{f.replace(str(USER_UPLOAD_DIR), '').lstrip('/')}"
                        for f in files
                        if str(USER_UPLOAD_DIR) in f
                    ]
                    human_content = {"message": message, "files": file_urls}
                else:
                    human_content = message

                await self.repository.add_message(thread_id, "human", human_content)
                await self.repository.add_message(thread_id, "ai", cached_resp)
                return thread_id, cached_resp

        # Prepare Graph State
        human_msg = await create_multimodal_message(message, files)
        initial_state = {
            "messages": [*history, human_msg],
            "research_output": "",
            "plan": "",
            "code": "",
            "thought": "Aura is analyzing...",
            "final_response": "",
            "next_step": "",
            "files": files,
            "model": model,
            "loop_count": 0,
        }

        from langchain_community.callbacks import get_openai_callback
        from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

        from src.multi_agent_rag.services.cost_service import cost_service

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(1, 2, 10),
                reraise=True,
            ):
                with attempt:
                    with get_openai_callback() as cb:
                        result = await self.graph.ainvoke(initial_state)
                        total_input, total_output = (
                            cb.prompt_tokens,
                            cb.completion_tokens,
                        )
                        actual_cost = cost_service.calculate_cost(
                            model or DEFAULT_MODEL, total_input, total_output
                        )
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            raise

        ai_content = {
            "thought": result.get("thought", ""),
            "research": result.get("research_output", ""),
            "plan": result.get("plan", ""),
            "code": result.get("code", ""),
            "response": result.get("final_response", "") or "Processed.",
        }

        # Cache Response
        if cache_service and cache_service.is_available:
            await cache_service.set_response_cache(request_hash, ai_content)

        if files:
            file_urls = [
                f"/user_upload/{f.replace(str(USER_UPLOAD_DIR), '').lstrip('/')}"
                for f in files
                if str(USER_UPLOAD_DIR) in f
            ]
            human_content = {"message": message, "files": file_urls}
        else:
            human_content = message

        await self.repository.add_message(thread_id, "human", human_content)
        await self.repository.add_message(
            thread_id,
            "ai",
            ai_content,
            input_tokens=total_input,
            output_tokens=total_output,
            cost=actual_cost,
        )
        return thread_id, ai_content

    async def stream_chat_flow(
        self,
        message: str,
        thread_id: str | None,
        files: list[str],
        model: str | None = None,
    ):
        """Executes a chat interaction and streams updates via SSE with caching."""
        # Ensure conversation exists
        if not thread_id:
            thread_id = str(uuid.uuid4())
            await self.repository.create_conversation(thread_id, "New Chat")
            await self._generate_and_update_title(
                thread_id, message, model or DEFAULT_MODEL
            )
        else:
            # Check if thread exists in DB
            existing = await self.repository.get_conversation(thread_id)
            if not existing:
                await self.repository.create_conversation(thread_id, "New Chat")
                await self._generate_and_update_title(
                    thread_id, message, model or DEFAULT_MODEL
                )

        db_messages = await self.repository.get_messages(thread_id)
        history = self._build_context_history(db_messages)

        # Check Cache
        request_hash = self._get_request_hash(message, history, files)
        if cache_service and cache_service.is_available:
            cached_resp = await cache_service.get_response_cache(request_hash)
            if cached_resp:
                logger.info(f"Response cache HIT (stream) for thread {thread_id}")
                yield f"data: {json.dumps({'thread_id': thread_id, 'final': cached_resp})}\n\n"
                return

        # Prepare State
        human_msg = await create_multimodal_message(message, files)
        initial_state = {
            "messages": [*history, human_msg],
            "research_output": "",
            "plan": "",
            "code": "",
            "thought": "Aura orchestrating...",
            "final_response": "",
            "next_step": "",
            "files": files,
            "model": model,
            "loop_count": 0,
        }

        if files:
            file_urls = [
                f"/user_upload/{f.replace(str(USER_UPLOAD_DIR), '').lstrip('/')}"
                for f in files
                if str(USER_UPLOAD_DIR) in f
            ]
            human_content = {"message": message, "files": file_urls}
        else:
            human_content = message

        await self.repository.add_message(thread_id, "human", human_content)
        from langchain_community.callbacks import get_openai_callback

        from src.multi_agent_rag.services.cost_service import cost_service

        last_state = dict(initial_state)
        # We need cb outside for tokens
        actual_cost = 0.0
        try:
            with get_openai_callback() as cb:
                async for output in self.graph.astream(initial_state):
                    for _, updates in output.items():
                        last_state.update(updates)
                        serializable = {
                            k: v
                            for k, v in updates.items()
                            if k != "messages" and not callable(v)
                        }
                        yield f"data: {json.dumps({'thread_id': thread_id, 'update': serializable})}\n\n"
                actual_cost = cost_service.calculate_cost(
                    model or DEFAULT_MODEL, cb.prompt_tokens, cb.completion_tokens
                )

                ai_content = {
                    "thought": last_state.get("thought", ""),
                    "research": last_state.get("research_output", ""),
                    "plan": last_state.get("plan", ""),
                    "code": last_state.get("code", ""),
                    "response": last_state.get("final_response", "") or "Done.",
                }

                if cache_service and cache_service.is_available:
                    await cache_service.set_response_cache(request_hash, ai_content)

                await self.repository.add_message(
                    thread_id,
                    "ai",
                    ai_content,
                    input_tokens=cb.prompt_tokens,
                    output_tokens=cb.completion_tokens,
                    cost=actual_cost,
                )
                yield f"data: {json.dumps({'thread_id': thread_id, 'final': ai_content})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'thread_id': thread_id, 'error': str(e)})}\n\n"
