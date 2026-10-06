import json
import time
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.sql_models import ConversationModel, MessageModel
from app.retrieval.retriever import retriever_service
from app.llm.client import llm_client
from app.schemas.chat import (
    ChatMessageRequest,
    ChatResponse,
    MessageResponse,
    ConversationResponse,
    ConversationDetailResponse,
)
from app.schemas.retrieval import Citation


class ChatService:
    def create_conversation(self, db: Session, title: str = "New Conversation") -> ConversationModel:
        conv = ConversationModel(title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def list_conversations(self, db: Session) -> List[ConversationResponse]:
        convs = db.query(ConversationModel).order_by(ConversationModel.updated_at.desc()).all()
        results = []
        for c in convs:
            results.append(
                ConversationResponse(
                    id=c.id,
                    title=c.title,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=len(c.messages),
                )
            )
        return results

    def get_conversation_detail(self, db: Session, conversation_id: str) -> Optional[ConversationDetailResponse]:
        conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
        if not conv:
            return None

        messages: List[MessageResponse] = []
        for m in conv.messages:
            citations_list = []
            if m.citations_json:
                try:
                    c_data = json.loads(m.citations_json)
                    citations_list = [Citation(**item) for item in c_data]
                except Exception:
                    citations_list = []

            messages.append(
                MessageResponse(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    citations=citations_list,
                    is_grounded=m.is_grounded,
                    confidence=m.confidence,
                    created_at=m.created_at,
                )
            )

        return ConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=messages,
        )

    def delete_conversation(self, db: Session, conversation_id: str) -> bool:
        conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

    def process_chat_message(self, db: Session, request: ChatMessageRequest) -> ChatResponse:
        start_time = time.time()

        # 1. Resolve or create conversation
        if request.conversation_id:
            conv = db.query(ConversationModel).filter(ConversationModel.id == request.conversation_id).first()
            if not conv:
                conv = self.create_conversation(db, title=request.message[:40])
        else:
            conv = self.create_conversation(db, title=request.message[:40])

        # 2. Extract recent conversation context for query reformulation
        recent_messages = conv.messages[-6:]  # last 3 turns
        chat_history_str = ""
        for m in recent_messages:
            role_prefix = "User" if m.role == "user" else "Assistant"
            chat_history_str += f"{role_prefix}: {m.content}\n"

        # 3. Query reformulation for conversational search
        rewritten_query = None
        if len(recent_messages) >= 2:
            rewritten_query = llm_client.reformulate_query(
                user_query=request.message,
                chat_history_str=chat_history_str,
            )
        search_query = rewritten_query or request.message

        # 4. Semantic retrieval and reranking
        retrieved_chunks, ret_latency = retriever_service.retrieve(
            query=search_query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            enable_reranking=request.enable_reranking,
            document_id_filter=request.document_id_filter,
        )

        # 5. Format prompt context
        formatted_context = retriever_service.format_context_for_prompt(retrieved_chunks)

        # 6. Grounded generation via LLM
        grounded_answer = llm_client.generate_grounded_answer(
            query=request.message,
            retrieved_chunks=retrieved_chunks,
            formatted_context=formatted_context,
        )

        # 7. Persist User Message
        user_msg = MessageModel(
            conversation_id=conv.id,
            role="user",
            content=request.message,
            is_grounded=True,
            confidence="high",
        )
        db.add(user_msg)

        # 8. Persist Assistant Message
        citations_data = [c.model_dump() for c in grounded_answer.citations]
        asst_msg = MessageModel(
            conversation_id=conv.id,
            role="assistant",
            content=grounded_answer.answer,
            citations_json=json.dumps(citations_data),
            is_grounded=grounded_answer.is_grounded,
            confidence=grounded_answer.confidence,
        )
        db.add(asst_msg)

        # Auto-update conversation title if it's the first message
        if len(conv.messages) <= 1:
            conv.title = request.message[:45] + ("..." if len(request.message) > 45 else "")

        db.commit()
        db.refresh(user_msg)
        db.refresh(asst_msg)

        total_latency_ms = (time.time() - start_time) * 1000.0

        return ChatResponse(
            conversation_id=conv.id,
            user_message=MessageResponse(
                id=user_msg.id,
                conversation_id=conv.id,
                role="user",
                content=user_msg.content,
                citations=[],
                is_grounded=True,
                confidence="high",
                created_at=user_msg.created_at,
            ),
            assistant_message=MessageResponse(
                id=asst_msg.id,
                conversation_id=conv.id,
                role="assistant",
                content=asst_msg.content,
                citations=grounded_answer.citations,
                is_grounded=grounded_answer.is_grounded,
                confidence=grounded_answer.confidence,
                created_at=asst_msg.created_at,
            ),
            retrieved_chunks=retrieved_chunks,
            rewritten_query=rewritten_query,
            execution_time_ms=round(total_latency_ms, 2),
        )


chat_service = ChatService()
