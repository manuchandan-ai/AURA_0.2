import json
import logging
from database import SessionLocal, Memory
from llm_router import run_llm_with_failover

logger = logging.getLogger("AURA-Memory")

class MemoryService:
    @staticmethod
    def get_all_memories(limit: int = 10) -> list:
        db = SessionLocal()
        try:
            records = db.query(Memory).order_by(Memory.id.desc()).limit(limit).all()
            return [{"id": m.id, "category": m.category, "fact": m.fact} for m in records]
        finally:
            db.close()

    @staticmethod
    def format_memory_context() -> str:
        memories = MemoryService.get_all_memories(limit=8)
        if not memories:
            return ""
        lines = [f"- [{m['category'].upper()}] {m['fact']}" for m in memories]
        return "Permanent User Context & Facts:\n" + "\n".join(lines) + "\n"

    @staticmethod
    def inspect_and_store(user_message: str):
        """Silently analyzes the prompt and saves long-term context."""
        # Fast filter: skip short or irrelevant messages
        if len(user_message.strip().split()) < 3 or user_message.lower().startswith("#goal"):
            return

        system_prompt = (
            "Analyze the user's message. Does it reveal any permanent personal attribute, preference, "
            "schedule constraint, skill level, or fitness/lifestyle background? "
            "Examples: 'I can only run in the mornings', 'I am fluent in Python', 'I dislike running on treadmills'.\n\n"
            "If YES, return a JSON object:\n"
            '{"has_memory": true, "category": "preference|skill|constraint|habit|fact", "fact": "Concise 1-sentence fact"}\n\n'
            "If NO permanent fact is present, return:\n"
            '{"has_memory": false}'
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        try:
            content, _ = run_llm_with_failover(messages, json_mode=True)
            data = json.loads(content)
            if data.get("has_memory") and data.get("fact"):
                db = SessionLocal()
                try:
                    new_mem = Memory(
                        category=data.get("category", "fact"),
                        fact=data.get("fact")
                    )
                    db.add(new_mem)
                    db.commit()
                    logger.info(f"Learned new memory: [{new_mem.category}] {new_mem.fact}")
                finally:
                    db.close()
        except Exception as e:
            logger.warning(f"Memory extraction skipped: {e}")