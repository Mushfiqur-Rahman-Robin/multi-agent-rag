import json
import uuid
from typing import List, Optional
from src.multi_agent_rag.repositories.chat_repository import ChatRepository
from src.multi_agent_rag.agents.graph import create_multi_agent_graph
from src.multi_agent_rag.core.multimodal import create_multimodal_message
from langchain_core.messages import HumanMessage, AIMessage

from src.multi_agent_rag.core.logging_config import logger

class ChatService:
    def __init__(self, repository: ChatRepository):
        self.repository = repository
        self.graph = create_multi_agent_graph()

    async def get_all_sessions(self):
        return await self.repository.get_conversations()

    async def get_session_history(self, thread_id: str):
        return await self.repository.get_messages(thread_id)

    async def delete_session(self, thread_id: str):
        await self.repository.delete_conversation(thread_id)

    async def run_chat_flow(self, message: str, thread_id: Optional[str], files: List[str], model: Optional[str] = None):
        logger.info(f"Initiating chat flow for message: '{message[:50]}...' (Thread: {thread_id})")
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
            logger.info(f"Creating new conversation with thread_id: {thread_id}")
            await self.repository.create_conversation(thread_id, message[:50])

        # Load and clean history
        db_messages = await self.repository.get_messages(thread_id)
        logger.info(f"Found {len(db_messages)} previous messages in thread {thread_id}")
        
        history = []
        for m in db_messages:
            raw_content = m.content
            # Extremely defensive content extraction
            content_obj = None
            if isinstance(raw_content, dict):
                content_obj = raw_content
            elif isinstance(raw_content, str):
                try:
                    content_obj = json.loads(raw_content)
                except Exception:
                    content_obj = raw_content # Fallback to literal string

            # Formatting for LangGraph history
            if m.role == "human":
                msg_text = str(content_obj) if not isinstance(content_obj, dict) else content_obj.get("message", str(content_obj))
                history.append(HumanMessage(content=msg_text))
            else:
                if isinstance(content_obj, dict):
                    # Prefer the textual response for LLM context, then code, then raw dump
                    msg_text = content_obj.get("response") or content_obj.get("code") or json.dumps(content_obj)
                else:
                    msg_text = str(content_obj)
                history.append(AIMessage(content=msg_text))

        # Create current message
        logger.info(f"Processing current multimodal message with {len(files)} attachments.")
        human_msg = create_multimodal_message(message, files)
        
        # Prepare Graph State
        initial_state = {
            "messages": history + [human_msg],
            "research_output": "",
            "plan": "",
            "code": "",
            "thought": "Thinking...",
            "final_response": "",
            "next_step": "",
            "files": files,
            "model": model
        }
        
        logger.info(f"Invoking Multi-Agent Graph for thread {thread_id}...")
        try:
            result = await self.graph.ainvoke(initial_state)
            logger.info(f"Graph execution complete for thread {thread_id}")
        except Exception as e:
            logger.error(f"Error during graph execution: {str(e)}", exc_info=True)
            raise

        # Map results to UI-ready structure
        research_out = result.get("research_output", "")
        plan_out = result.get("plan", "")
        code_out = result.get("code", "")
        final_out = result.get("final_response", "")
        
        # In interactive mode, we want the agent's explicit final_response
        main_response = final_out or "Task stage completed. What would you like to do next?"

        ai_content = {
            "thought": result.get("thought", "Thinking..."),
            "research": research_out,
            "plan": plan_out,
            "code": code_out,
            "response": main_response
        }

        # LOG EVERYTHING clearly
        logger.info(f"--- AGENT LOGS FOR THREAD {thread_id} ---")
        logger.info(f"THOUGHT: {ai_content['thought']}")
        logger.info(f"RESPONSE READY: {bool(ai_content['response'])}")
        logger.debug(f"FULL PAYLOAD: {json.dumps(ai_content)}")
        logger.info(f"----------------------------------------")

        # Persist to Database
        try:
            await self.repository.add_message(thread_id, "human", message)
            await self.repository.add_message(thread_id, "ai", ai_content)
            logger.info(f"Messages persisted successfully for thread {thread_id}")
        except Exception as e:
            logger.error(f"Persistence error: {str(e)}", exc_info=True)

        return thread_id, ai_content

    async def stream_chat_flow(self, message: str, thread_id: Optional[str], files: List[str], model: Optional[str] = None):
        if not thread_id:
            thread_id = str(uuid.uuid4())
            await self.repository.create_conversation(thread_id, message[:50])

        db_messages = await self.repository.get_messages(thread_id)
        history = []
        for m in db_messages:
            raw_content = m.content
            content_obj = None
            if isinstance(raw_content, dict):
                content_obj = raw_content
            elif isinstance(raw_content, str):
                try:
                    content_obj = json.loads(raw_content)
                except Exception:
                    content_obj = raw_content

            if m.role == "human":
                msg_text = str(content_obj) if not isinstance(content_obj, dict) else content_obj.get("message", str(content_obj))
                history.append(HumanMessage(content=msg_text))
            else:
                if isinstance(content_obj, dict):
                    msg_text = content_obj.get("response") or content_obj.get("code") or json.dumps(content_obj)
                else:
                    msg_text = str(content_obj)
                history.append(AIMessage(content=msg_text))

        human_msg = create_multimodal_message(message, files)
        initial_state = {
            "messages": history + [human_msg],
            "research_output": "",
            "plan": "",
            "code": "",
            "thought": "Aura is orchestrating agents...",
            "final_response": "",
            "next_step": "",
            "files": files,
            "model": model
        }

        # Persist human message early
        await self.repository.add_message(thread_id, "human", message)

        last_state = initial_state
        async for output in self.graph.astream(initial_state):
            # output is a dict like {'node_name': {state_updates}}
            for key, val in output.items():
                last_state.update(val)
                # Filter out non-serializable objects (like LangChain messages)
                serializable_update = {k: v for k, v in val.items() if k != "messages"}
                # Stream the update to frontend
                yield f"data: {json.dumps({'thread_id': thread_id, 'update': serializable_update})}\n\n"

        # Map final results
        ai_content = {
            "thought": last_state.get("thought", ""),
            "research": last_state.get("research_output", ""),
            "plan": last_state.get("plan", ""),
            "code": last_state.get("code", ""),
            "response": last_state.get("final_response", "") or "Stage completed."
        }
        
        await self.repository.add_message(thread_id, "ai", ai_content)
        yield f"data: {json.dumps({'thread_id': thread_id, 'final': ai_content})}\n\n"
