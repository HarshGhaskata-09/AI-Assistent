# modules/activity_integration.py - Integration of Activity Tracking with AI Assistent

from modules.activity_tracker import ActivityTracker
from database.db_manager import DatabaseManager
from datetime import datetime
import threading

class ActivityIntegration:
    """
    Integrates activity tracking with CommandProcessor
    Automatically tracks all activities without user intervention
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize activity integration"""
        self.tracker = ActivityTracker()
        self.db = db_manager or DatabaseManager()
        self.background_thread = None
        self.running = False
    
    def track_command_execution(self, command_data: dict, response: str, execution_time_ms: int = 0):
        """
        Track command execution
        Called after every command is executed
        """
        try:
            command_type = command_data.get('intent', 'unknown')
            success = command_data.get('confidence', 0) > 0.5
            
            # Track in activity tracker
            self.tracker.track_command_usage(
                command_type=command_type,
                success=success,
                processing_time_ms=execution_time_ms
            )
            
            # Learn habits from repeated commands
            self._learn_habits_from_command(command_type)
            
        except Exception as e:
            print(f"Error tracking command: {e}")
    
    def track_app_launch(self, app_name: str, category: str = "general", duration_seconds: int = 0):
        """
        Track application launch
        Called when user opens an app through AI Assistent
        """
        try:
            self.tracker.track_app_usage(
                app_name=app_name,
                duration_seconds=duration_seconds,
                category=category
            )
            
            # Learn habits from app usage
            self._learn_habits_from_app(app_name)
            
        except Exception as e:
            print(f"Error tracking app: {e}")
    
    def _learn_habits_from_command(self, command_type: str):
        """Learn habits from command usage"""
        habit_name = f"command_{command_type}"
        self.tracker.learn_habit(
            habit_name=habit_name,
            command_type=command_type,
            frequency=1
        )
    
    def _learn_habits_from_app(self, app_name: str):
        """Learn habits from app usage"""
        habit_name = f"app_{app_name}"
        self.tracker.learn_habit(
            habit_name=habit_name,
            command_type="open_app",
            frequency=1
        )
    
    def get_daily_summary(self) -> dict:
        """Get today's activity summary"""
        return self.tracker.generate_daily_summary()
    
    def get_weekly_summary(self) -> dict:
        """Get weekly activity summary"""
        return self.tracker.get_weekly_summary()
    
    def get_productivity_report(self, period: str = "daily") -> dict:
        """Get productivity report"""
        return self.tracker.generate_productivity_report(period)
    
    def get_habits(self) -> list:
        """Get learned habits"""
        return self.tracker.get_habits()
    
    def predict_next_action(self) -> dict:
        """Predict user's next likely action"""
        return self.tracker.predict_next_action()
    
    def get_most_used_apps(self, days: int = 7, limit: int = 10) -> list:
        """Get most used apps"""
        return self.tracker.get_most_used_apps(days, limit)
    
    def start_background_tracking(self):
        """Start background activity tracking"""
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(
                target=self._background_tracking_loop,
                daemon=True
            )
            self.background_thread.start()
            print("OK: Background activity tracking started")
    
    def stop_background_tracking(self):
        """Stop background activity tracking"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        print("OK: Background activity tracking stopped")
    
    def _background_tracking_loop(self):
        """Background loop for periodic tracking tasks"""
        import time
        
        while self.running:
            try:
                # Every hour, generate daily summary if not already done
                current_hour = datetime.now().hour
                if current_hour % 6 == 0:  # Every 6 hours
                    summary = self.tracker.generate_daily_summary()
                    # Could send notification here
                
                time.sleep(3600)  # Check every hour
            except Exception as e:
                print(f"Error in background tracking: {e}")
                time.sleep(60)


class ActivityReporter:
    """
    Generates and formats activity reports for display
    """
    
    def __init__(self, activity_integration: ActivityIntegration):
        """Initialize activity reporter"""
        self.activity = activity_integration
    
    def format_daily_summary(self) -> str:
        """Format daily summary as readable text"""
        summary = self.activity.get_daily_summary()
        
        if 'message' in summary:
            return summary['message']
        
        report = f"""
=== DAILY ACTIVITY SUMMARY ===
Date: {summary.get('date')} ({summary.get('day_of_week')})

COMMANDS:
  Total: {summary.get('total_commands')}
  Successful: {summary.get('successful_commands')}
  Success Rate: {summary.get('success_rate')}%
  Avg Response Time: {summary.get('avg_response_time_ms')}ms

APPS:
  Total Apps Used: {summary.get('apps_used')}
  Total Launches: {summary.get('total_app_launches')}

ACTIVITY LEVEL: {summary.get('activity_level')}

TOP APPS:
{self._format_list(summary.get('top_apps', []))}

TOP COMMANDS:
{self._format_list(summary.get('top_commands', []))}
"""
        return report
    
    def format_weekly_summary(self) -> str:
        """Format weekly summary as readable text"""
        summary = self.activity.get_weekly_summary()
        
        report = f"""
=== WEEKLY ACTIVITY SUMMARY ===
Week: {summary.get('week_start')} to {summary.get('week_end')}

METRICS:
  Total Commands: {summary.get('total_commands')}
  Avg Success Rate: {summary.get('avg_success_rate')}%
  Total Apps Used: {summary.get('total_apps_used')}
  Most Active Day: {summary.get('most_active_day', {}).get('day_of_week', 'N/A')}

DAILY BREAKDOWN:
"""
        for day in summary.get('daily_summaries', []):
            report += f"  {day['date']}: {day['total_commands']} commands ({day['success_rate']}% success)\n"
        
        return report
    
    def format_productivity_report(self, period: str = "daily") -> str:
        """Format productivity report"""
        report_data = self.activity.get_productivity_report(period)
        
        report = f"""
=== PRODUCTIVITY REPORT ({period.upper()}) ===
Period: {report_data.get('period')}
"""
        
        if period == "daily":
            report += f"Date: {report_data.get('date')}\n"
        elif period == "weekly":
            report += f"Week: {report_data.get('week_start')} to {report_data.get('week_end')}\n"
        elif period == "monthly":
            report += f"Month: {report_data.get('month')}\n"
        
        report += "\nMETRICS:\n"
        for key, value in report_data.get('metrics', {}).items():
            report += f"  {key}: {value}\n"
        
        if report_data.get('insights'):
            report += "\nINSIGHTS:\n"
            for insight in report_data.get('insights', []):
                report += f"  - {insight}\n"
        
        if report_data.get('recommendations'):
            report += "\nRECOMMENDATIONS:\n"
            for rec in report_data.get('recommendations', []):
                report += f"  - {rec}\n"
        
        return report
    
    def format_habits(self) -> str:
        """Format learned habits"""
        habits = self.activity.get_habits()
        
        if not habits:
            return "No habits learned yet. Keep using AI Assistent to build habits!"
        
        report = "=== LEARNED HABITS ===\n\n"
        
        for habit in habits:
            report += f"Habit: {habit['name']}\n"
            report += f"  Type: {habit['command_type']}\n"
            report += f"  Occurrences: {habit['occurrences']}\n"
            report += f"  Confidence: {habit['confidence']*100:.0f}%\n"
            report += f"  Status: {habit['status']}\n"
            report += f"  Days Active: {habit['days_active']}\n"
            report += f"  Last Used: {habit['last_occurrence']}\n\n"
        
        return report
    
    def format_app_usage(self, days: int = 7) -> str:
        """Format app usage report"""
        apps = self.activity.get_most_used_apps(days, limit=10)
        
        if not apps:
            return "No app usage recorded."
        
        report = f"=== TOP APPS (Last {days} days) ===\n\n"
        
        for i, app in enumerate(apps, 1):
            report += f"{i}. {app['app']}\n"
            report += f"   Launches: {app['launches']}\n"
            report += f"   Time: {app['total_time_minutes']} minutes\n"
            report += f"   Category: {app['category']}\n\n"
        
        return report
    
    def _format_list(self, items: list) -> str:
        """Format list of items"""
        if not items:
            return "  None"
        
        result = ""
        for item in items:
            if isinstance(item, dict):
                if 'name' in item:
                    result += f"  - {item['name']}: {item.get('count', 0)}\n"
                elif 'command' in item:
                    result += f"  - {item['command']}: {item.get('count', 0)}\n"
                elif 'app' in item:
                    result += f"  - {item['app']}: {item.get('launches', 0)}\n"
        
        return result if result else "  None"
