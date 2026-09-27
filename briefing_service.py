import json
import logging
from datetime import datetime
from database import SessionLocal, Goal, Milestone, Reminder, Memory
from llm_router import run_llm_with_failover

logger = logging.getLogger("AURA-Briefing")

class BriefingService:
    @staticmethod
    def generate_morning_briefing() -> dict:
        db = SessionLocal()
        try:
            goals = db.query(Goal).all()
            reminders = db.query(Reminder).filter(Reminder.is_completed == False).all()
            memories = db.query(Memory).order_by(Memory.id.desc()).limit(5).all()

            if not goals and not reminders:
                return {
                    "headline": "Good Day, Operator",
                    "status_summary": "All systems nominal. Ready to calibrate new objectives.",
                    "focus_tasks": ["Set your primary #goal in the chat terminal"],
                    "on_track_ratio": "0/0"
                }

            # Compile compact context for LLM
            goals_summary = [f"- {g.intention} (Progress: {g.progress_percentage}%, Streak: {g.streak_count}d)" for g in goals]
            reminders_summary = [f"- {r.task_text} [{r.priority} Priority, Due: {r.due_info}]" for r in reminders]
            memories_summary = [f"- {m.fact}" for m in memories]

            prompt = (
                "You are AURA's Executive Dispatcher. Based on the user's active goals and tasks, "
                "generate an inspiring, concise morning executive briefing.\n"
                "Return ONLY a JSON object with keys:\n"
                "- 'greeting' (e.g. 'Good Morning, John')\n"
                "- 'status_summary' (1 crisp sentence assessing schedule momentum)\n"
                "- 'focus_directive' (a concise 1-sentence primary mission for today)\n\n"
                f"Active Goals:\n" + "\n".join(goals_summary) + "\n\n"
                f"Pending Reminders:\n" + "\n".join(reminders_summary) + "\n\n"
                f"User Profile Constraints:\n" + "\n".join(memories_summary)
            )

            messages = [{"role": "system", "content": prompt}]
            content, _ = run_llm_with_failover(messages, json_mode=True)
            data = json.loads(content)

            total_goals = len(goals)
            active_streaks = len([g for g in goals if g.streak_count > 0])

            return {
                "headline": data.get("greeting", "Good Morning, John"),
                "status_summary": data.get("status_summary", "Your goals are actively moving forward."),
                "focus_directive": data.get("focus_directive", "Execute on your primary milestone."),
                "on_track_ratio": f"{active_streaks}/{total_goals}"
            }
        except Exception as e:
            logger.error(f"Error generating briefing: {e}")
            return {
                "headline": "Good Morning, John",
                "status_summary": "Your goals are on track!",
                "focus_directive": "Maintain daily habit consistency.",
                "on_track_ratio": f"{len(goals)} active"
            }
        finally:
            db.close()

    @staticmethod
    def recalibrate_goal(goal_id: int) -> dict:
        db = SessionLocal()
        try:
            goal = db.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                return {"error": "Goal not found"}

            uncompleted = [m.phase_title for m in goal.milestones if not m.is_completed]
            
            prompt = (
                f"The user is falling behind or broke their streak on goal: '{goal.intention}'. "
                f"Original timeline was '{goal.timeline}'. Unfinished milestones: {uncompleted}. "
                "Recalibrate this plan with a reduced friction, realistic pace. "
                "Return ONLY a JSON object with keys: "
                "'new_timeline' (string), 'encouragement' (1 short sentence), and "
                "'realigned_phases' (list of 3-5 restructured milestone strings)."
            )

            messages = [{"role": "system", "content": prompt}]
            content, _ = run_llm_with_failover(messages, json_mode=True)
            data = json.loads(content)

            # Update database with recalibrated plan
            goal.timeline = data.get("new_timeline", goal.timeline)
            
            # Remove old uncompleted milestones and inject adjusted ones
            for m in list(goal.milestones):
                if not m.is_completed:
                    db.delete(m)

            for phase in data.get("realigned_phases", []):
                db.add(Milestone(goal_id=goal.id, phase_title=phase, is_completed=False))

            db.commit()
            return {
                "goal_id": goal.id,
                "realigned_timeline": goal.timeline,
                "note": data.get("encouragement", "Plan adapted to your current pace.")
            }
        finally:
            db.close()