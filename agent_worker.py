from datetime import date, timedelta, datetime
import logging
from database import SessionLocal, User, Goal, Reminder
from llm_router import run_llm_with_failover

logger = logging.getLogger("AURA-Agent")

class AutonomousAgent:
    @staticmethod
    def midnight_decay_and_alert():
        """Midnight cron evaluating streak decay, freeze shield consumption, and recovery challenges."""
        db = SessionLocal()
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            goals = db.query(Goal).all()

            for g in goals:
                # If checked in today or yesterday, streak is safe
                if g.last_check_in_date in [today, yesterday]:
                    continue

                user = db.query(User).filter(User.id == g.user_id).first()
                if not user:
                    continue

                # Scenario 1: User has an active Freeze Token -> Defend streak
                if user.freeze_tokens > 0:
                    user.freeze_tokens -= 1
                    g.streak_frozen = True
                    g.last_check_in_date = yesterday  # Grant 1-day grace period
                    
                    alert = Reminder(
                        user_id=user.id,
                        task_text=f"🛡️ Freeze Shield consumed for goal '{g.intention[:25]}...'. Streak saved at {g.streak_count}d!",
                        priority="Medium",
                        due_info="Today",
                        is_completed=False
                    )
                    db.add(alert)
                    logger.info(f"Consumed freeze token for user {user.username} on goal {g.id}")

                # Scenario 2: No tokens left -> Streak decays, activate Recovery Challenge
                else:
                    if g.streak_count > 0:
                        g.saved_streak_count = g.streak_count
                        g.streak_count = 0
                        g.in_recovery = True
                        
                        # Generate contextual micro-challenge via LLM
                        prompt = (
                            f"Generate a single, bite-sized (10-minute) recovery challenge task for someone who lapsed on their goal: '{g.intention}'. "
                            "It should be easy and encouraging. Output ONLY the short task description."
                        )
                        challenge_text, _ = run_llm_with_failover([{"role": "user", "content": prompt}], json_mode=False)
                        g.recovery_task = challenge_text.strip().replace('"', '')

                        alert = Reminder(
                            user_id=user.id,
                            task_text=f"⚠️ Streak lapsed on '{g.intention[:20]}...'. Complete the Recovery Challenge to restore {g.saved_streak_count}d!",
                            priority="High",
                            due_info="Today",
                            is_completed=False
                        )
                        db.add(alert)
                        logger.info(f"Goal {g.id} entered recovery mode for user {user.username}")

            db.commit()
        except Exception as e:
            logger.error(f"Error in midnight_decay_and_alert: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def audit_and_nudge():
        """Morning cron creating motivational notifications and generating new daily tasks."""
        db = SessionLocal()
        try:
            today = date.today()
            users = db.query(User).all()
            for u in users:
                pending_goals = db.query(Goal).filter(Goal.user_id == u.id).all()
                for g in pending_goals:
                    if g.progress_percentage >= 100:
                        continue
                        
                    # Determine context based on existing routine
                    context = g.daily_routine if getattr(g, 'daily_routine', None) else g.intention
                    prompt = (
                        f"The user is working on the goal: '{g.intention}'.\n"
                        f"Their progress is {g.progress_percentage}%.\n"
                        f"Context/Roadmap:\n{context}\n\n"
                        "Generate ONE single, actionable, highly specific task that the user should do TODAY to move this goal forward. "
                        "Output ONLY the task description, maximum 15 words."
                    )
                    
                    try:
                        task_text, _ = run_llm_with_failover([{"role": "user", "content": prompt}], json_mode=False)
                        clean_task = task_text.strip().replace('"', '')
                        
                        exists = db.query(Reminder).filter(
                            Reminder.user_id == u.id, 
                            Reminder.task_text == clean_task,
                            Reminder.is_completed == False
                        ).first()
                        
                        if not exists and clean_task:
                            db.add(Reminder(
                                user_id=u.id,
                                task_text=f"🎯 Daily Task: {clean_task}",
                                priority="High",
                                due_info="Today"
                            ))
                            logger.info(f"Generated daily task for user {u.username} on goal {g.id}: {clean_task}")
                    except Exception as llm_e:
                        logger.warning(f"Failed to generate daily task for goal {g.id}: {llm_e}")
                        
            db.commit()
        except Exception as e:
            logger.error(f"Error in audit_and_nudge: {e}")
            db.rollback()
        finally:
            db.close()