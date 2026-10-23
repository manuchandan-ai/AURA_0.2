from datetime import date, timedelta
import logging
from database import SessionLocal, User, Goal, Reminder
from llm_router import run_llm_with_failover

logger = logging.getLogger("AURA-Agent")

class AutonomousAgent:
    @staticmethod
    def midnight_decay_and_alert():
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        goals_to_recover = []
        with SessionLocal() as db:
            try:
                goals = db.query(Goal).all()
                for g in goals:
                    if g.last_check_in_date in [today, yesterday]:
                        continue
                    user = db.query(User).filter(User.id == g.user_id).first()
                    if not user:
                        continue

                    if user.freeze_tokens > 0:
                        user.freeze_tokens -= 1
                        g.streak_frozen = True
                        g.last_check_in_date = yesterday
                        db.add(Reminder(
                            user_id=user.id,
                            task_text=f"🛡️ Freeze Shield consumed for goal '{g.intention[:25]}...'.",
                            priority="Medium",
                            due_info="Today",
                            is_completed=False
                        ))
                    else:
                        if g.streak_count > 0:
                            goals_to_recover.append((g.id, user.id, g.intention, g.streak_count))
                db.commit()
            except Exception as e:
                logger.error(f"Error reading goals in midnight_decay: {e}")
                db.rollback()

        recovered_data = []
        for goal_id, user_id, intention, streak in goals_to_recover:
            prompt = (
                f"Generate a single, bite-sized (10-minute) recovery challenge task for someone who lapsed on their goal: '{intention}'. "
                "Output ONLY the short task description, max 15 words."
            )
            try:
                challenge, _ = run_llm_with_failover([{"role": "user", "content": prompt}], json_mode=False)
                clean_challenge = challenge.strip().replace('"', '')
            except Exception:
                clean_challenge = "Spend 10 minutes reviewing your core milestone."
            recovered_data.append((goal_id, user_id, intention, streak, clean_challenge))

        if recovered_data:
            with SessionLocal() as db:
                try:
                    for goal_id, user_id, intention, streak, challenge in recovered_data:
                        target_goal = db.query(Goal).filter(Goal.id == goal_id).first()
                        if target_goal:
                            target_goal.saved_streak_count = streak
                            target_goal.streak_count = 0
                            target_goal.in_recovery = True
                            target_goal.recovery_task = challenge
                            db.add(Reminder(
                                user_id=user_id,
                                task_text=f"⚠️ Streak lapsed on '{intention[:20]}...': {challenge}",
                                priority="High",
                                due_info="Today",
                                is_completed=False
                            ))
                    db.commit()
                except Exception as e:
                    logger.error(f"Error applying recovery challenges: {e}")
                    db.rollback()

    @staticmethod
    def audit_and_nudge():
        """Morning cron creating motivational notifications and generating new daily tasks."""
        today = date.today()
        user_goals_map = []
        
        with SessionLocal() as db:
            try:
                users = db.query(User).all()
                for u in users:
                    pending_goals = db.query(Goal).filter(Goal.user_id == u.id).all()
                    for g in pending_goals:
                        if g.progress_percentage < 100:
                            context = getattr(g, 'daily_routine', None) or g.intention
                            user_goals_map.append((u.id, u.username, g.id, g.intention, g.progress_percentage, context))
            except Exception as e:
                logger.error(f"Error fetching goals for audit_and_nudge: {e}")
                return

        generated_tasks = []
        for user_id, username, goal_id, intention, progress, context in user_goals_map:
            prompt = (
                f"The user is working on the goal: '{intention}'.\n"
                f"Their progress is {progress}%.\n"
                f"Context/Roadmap:\n{context}\n\n"
                "Generate ONE single, actionable, highly specific task that the user should do TODAY to move this goal forward. "
                "Output ONLY the task description, maximum 15 words."
            )
            try:
                task_text, _ = run_llm_with_failover([{"role": "user", "content": prompt}], json_mode=False)
                clean_task = task_text.strip().replace('"', '')
                if clean_task:
                    generated_tasks.append((user_id, goal_id, clean_task))
            except Exception as llm_e:
                logger.warning(f"Failed to generate daily task for goal {goal_id}: {llm_e}")

        if generated_tasks:
            with SessionLocal() as db:
                try:
                    for user_id, goal_id, clean_task in generated_tasks:
                        exists = db.query(Reminder).filter(
                            Reminder.user_id == user_id,
                            Reminder.task_text == f"🎯 Daily Task: {clean_task}",
                            Reminder.is_completed == False
                        ).first()
                        if not exists:
                            db.add(Reminder(
                                user_id=user_id,
                                goal_id=goal_id,
                                task_text=f"🎯 Daily Task: {clean_task}",
                                priority="High",
                                due_info="Today"
                            ))
                    db.commit()
                except Exception as e:
                    logger.error(f"Error committing daily nudges: {e}")
                    db.rollback()