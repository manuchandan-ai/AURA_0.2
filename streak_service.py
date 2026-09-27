from datetime import date, timedelta
from sqlalchemy.orm import Session
from database import Goal

class StreakService:
    @staticmethod
    def register_user_activity(goal: Goal, db: Session) -> dict:
        """
        Called when a user logs progress, completes a milestone,
        or chats via #goal.
        """
        today = date.today()

        # Case 1: Already checked in today
        if goal.last_check_in_date == today:
            return {
                "status": "already_logged",
                "streak": goal.streak_count,
                "message": "Activity already recorded for today."
            }

        yesterday = today - timedelta(days=1)

        # Case 2: Consecutive check-in (yesterday -> today)
        if goal.last_check_in_date == yesterday:
            goal.streak_count += 1
            status_msg = "Streak extended!"
        
        # Case 3: First time ever or recovered streak
        elif goal.last_check_in_date is None:
            goal.streak_count = 1
            status_msg = "Streak started!"
        
        # Case 4: Broken streak (missed yesterday)
        else:
            goal.streak_count = 1
            status_msg = "Streak reset to 1 day."

        goal.last_check_in_date = today
        db.commit()
        db.refresh(goal)

        return {
            "status": "success",
            "streak": goal.streak_count,
            "message": status_msg
        }

    @staticmethod
    def run_midnight_decay_audit(db: Session):
        """
        Scheduled cron task: Checks all active goals.
        If last_check_in_date < yesterday, streak drops to 0.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        goals = db.query(Goal).all()
        decayed_count = 0

        for goal in goals:
            # If no check-in yesterday and streak is greater than 0
            if goal.last_check_in_date and goal.last_check_in_date < yesterday:
                if goal.streak_frozen:
                    # Streak freeze prevents reset once
                    goal.streak_frozen = False
                else:
                    goal.streak_count = 0
                    decayed_count += 1

        db.commit()
        print(f"[AURA CRON] Midnight audit completed. {decayed_count} goal streaks decayed.")