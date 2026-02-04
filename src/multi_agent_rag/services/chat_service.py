import json
import uuid
from typing import List, Optional
from src.multi_agent_rag.repositories.chat_repository import ChatRepository
from src.multi_agent_rag.agents.graph import create_multi_agent_graph
from src.multi_agent_rag.core.multimodal import create_multimodal_message
from langchain_core.messages import HumanMessage, AIMessage

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

    async def run_chat_flow(self, message: str, thread_id: Optional[str], files: List[str]):
        if not thread_id:
            thread_id = str(uuid.uuid4())
            await self.repository.create_conversation(thread_id, message[:50])

        # Load history
        db_messages = await self.repository.get_messages(thread_id)
        history = []
        for m in db_messages:
            content = json.loads(m.content) if isinstance(m.content, str) else m.content
            if m.role == "human":
                history.append(HumanMessage(content=content))
            else:
                history.append(AIMessage(content=content))

        # Create message
        human_msg = create_multimodal_message(message, files)
        
        # Run graph
        initial_state = {
            "messages": history + [human_msg],
            "research_output": "",
            "plan": "",
            "code": "",
            "next_step": "",
            "files": files
        }
        
        result = await self.graph.ainvoke(initial_state)

        # Persistence
        ai_content = {
            "research": result["research_output"],
            "plan": result["plan"],
            "code": result["code"]
        }
        
        await self.repository.add_message(thread_id, "human", message)
        await self.repository.add_message(thread_id, "ai", ai_content)

        return thread_id, ai_content
