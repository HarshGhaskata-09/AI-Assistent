# modules/voice_reports.py - Voice-based Activity Report Reading

from modules.activity_integration import ActivityIntegration, ActivityReporter
from modules.voice import VoiceHandler
from datetime import datetime

class VoiceReportReader:
    """
    Reads activity reports aloud using text-to-speech
    Converts reports to natural, conversational speech
    """
    
    def __init__(self, voice_handler: VoiceHandler = None, activity_integration: ActivityIntegration = None):
        """Initialize voice report reader"""
        self.voice = voice_handler
        self.activity = activity_integration or ActivityIntegration()
        self.reporter = ActivityReporter(self.activity)
    
    def read_daily_summary(self):
        """Read today's activity summary aloud"""
        summary = self.activity.get_daily_summary()
        
        if 'message' in summary:
            speech_text = summary['message']
        else:
            speech_text = self._format_daily_summary_for_speech(summary)
        
        if self.voice:
            self.voice.speak(speech_text)
        
        return speech_text
    
    def read_weekly_summary(self):
        """Read weekly activity summary aloud"""
        summary = self.activity.get_weekly_summary()
        speech_text = self._format_weekly_summary_for_speech(summary)
        
        if self.voice:
            self.voice.speak(speech_text)
        
        return speech_text
    
    def read_productivity_report(self, period: str = "daily"):
        """Read productivity report aloud"""
        report = self.activity.get_productivity_report(period)
        speech_text = self._format_productivity_report_for_speech(report, period)
        
        if self.voice:
            self.voice.speak(speech_text)
        
        return speech_text
    
    def read_habits(self):
        """Read learned habits aloud"""
        habits = self.activity.get_habits()
        speech_text = self._format_habits_for_speech(habits)
        
        if self.voice:
            self.voice.speak(speech_text)
        
        return speech_text
    
    def read_app_usage(self, days: int = 7):
        """Read app usage statistics aloud"""
        apps = self.activity.get_most_used_apps(days, limit=5)
        speech_text = self._format_app_usage_for_speech(apps, days)
        
        if self.voice:
            self.voice.speak(speech_text)
        
        return speech_text
    
    def read_prediction(self):
        """Read predicted next action aloud"""
        prediction = self.activity.predict_next_action()
        
        if prediction:
            speech_text = self._format_prediction_for_speech(prediction)
        else:
            speech_text = "I haven't learned enough about your habits yet. Keep using me and I'll start making predictions!"
        
        if self.voice:
            self.voice.speak(speech_text)
        
        return speech_text
    
    # ============================================================
    # FORMATTING METHODS FOR NATURAL SPEECH
    # ============================================================
    
    def _format_daily_summary_for_speech(self, summary: dict) -> str:
        """Format daily summary for natural speech"""
        day = summary.get('day_of_week', 'today')
        
        speech = f"Here's your activity summary for {day}. "
        
        # Commands summary
        total_cmds = summary.get('total_commands', 0)
        success_rate = summary.get('success_rate', 0)
        speech += f"You gave me {total_cmds} commands with a {success_rate} percent success rate. "
        
        # Apps summary
        apps_used = summary.get('apps_used', 0)
        app_launches = summary.get('total_app_launches', 0)
        speech += f"You used {apps_used} different apps with a total of {app_launches} launches. "
        
        # Activity level
        activity_level = summary.get('activity_level', 'moderate')
        speech += f"Your activity level was {activity_level}. "
        
        # Response time
        avg_time = summary.get('avg_response_time_ms', 0)
        speech += f"My average response time was {round(avg_time)} milliseconds. "
        
        # Top apps
        top_apps = summary.get('top_apps', [])
        if top_apps:
            app_names = [app['name'] for app in top_apps[:3]]
            speech += f"Your top apps were {', '.join(app_names)}. "
        
        # Top commands
        top_cmds = summary.get('top_commands', [])
        if top_cmds:
            cmd_names = [cmd['command'] for cmd in top_cmds[:2]]
            speech += f"Your most used commands were {' and '.join(cmd_names)}. "
        
        return speech
    
    def _format_weekly_summary_for_speech(self, summary: dict) -> str:
        """Format weekly summary for natural speech"""
        week_start = summary.get('week_start', 'this week')
        total_cmds = summary.get('total_commands', 0)
        avg_success = summary.get('avg_success_rate', 0)
        total_apps = summary.get('total_apps_used', 0)
        
        speech = f"Here's your weekly activity summary for the week starting {week_start}. "
        speech += f"You gave me a total of {total_cmds} commands with an average success rate of {avg_success} percent. "
        speech += f"You used {total_apps} different applications throughout the week. "
        
        # Most active day
        most_active = summary.get('most_active_day')
        if most_active:
            most_active_day = most_active.get('day_of_week', 'a day')
            most_active_cmds = most_active.get('total_commands', 0)
            speech += f"Your most active day was {most_active_day} with {most_active_cmds} commands. "
        
        return speech
    
    def _format_productivity_report_for_speech(self, report: dict, period: str) -> str:
        """Format productivity report for natural speech"""
        speech = f"Here's your {period} productivity report. "
        
        metrics = report.get('metrics', {})
        
        # Total commands
        total = metrics.get('total_commands', 0)
        speech += f"You executed {total} commands. "
        
        # Success rate
        success = metrics.get('success_rate', 0)
        speech += f"Your success rate was {success} percent. "
        
        # Response time
        if 'avg_response_time_ms' in metrics:
            response_time = metrics.get('avg_response_time_ms', 0)
            speech += f"Average response time was {round(response_time)} milliseconds. "
        
        # Activity level
        activity = metrics.get('activity_level', 'moderate')
        speech += f"Your activity level was {activity}. "
        
        # Insights
        insights = report.get('insights', [])
        if insights:
            speech += "Here are some insights: "
            for insight in insights[:2]:
                speech += f"{insight} "
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            speech += "Here are my recommendations: "
            for rec in recommendations[:2]:
                speech += f"{rec} "
        
        return speech
    
    def _format_habits_for_speech(self, habits: list) -> str:
        """Format habits for natural speech"""
        if not habits:
            return "I haven't learned any habits yet. Keep using me and I'll start learning your patterns!"
        
        established = [h for h in habits if h['status'] == 'established']
        forming = [h for h in habits if h['status'] == 'forming']
        learning = [h for h in habits if h['status'] == 'learning']
        
        speech = f"I've learned {len(habits)} habits about you. "
        
        if established:
            speech += f"I've established {len(established)} habits: "
            habit_names = [h['name'].replace('command_', '').replace('app_', '') for h in established[:3]]
            speech += f"{', '.join(habit_names)}. "
        
        if forming:
            speech += f"I'm forming {len(forming)} new habits. "
        
        if learning:
            speech += f"I'm learning {len(learning)} patterns. "
        
        # Top habit
        if habits:
            top_habit = habits[0]
            confidence = round(top_habit['confidence'] * 100)
            speech += f"Your strongest habit is {top_habit['name']} with {confidence} percent confidence. "
        
        return speech
    
    def _format_app_usage_for_speech(self, apps: list, days: int) -> str:
        """Format app usage for natural speech"""
        if not apps:
            return f"You haven't used any apps in the last {days} days."
        
        speech = f"Here are your most used apps in the last {days} days. "
        
        for i, app in enumerate(apps[:5], 1):
            app_name = app['app']
            launches = app['launches']
            time_minutes = app['total_time_minutes']
            
            speech += f"Number {i}: {app_name} with {launches} launches and {round(time_minutes)} minutes of usage. "
        
        return speech
    
    def _format_prediction_for_speech(self, prediction: dict) -> str:
        """Format prediction for natural speech"""
        action = prediction.get('predicted_action', 'unknown')
        confidence = round(prediction.get('confidence', 0) * 100)
        occurrences = prediction.get('based_on_occurrences', 0)
        
        speech = f"Based on your habits, I predict you might want to {action} next. "
        speech += f"I'm {confidence} percent confident about this prediction based on {occurrences} previous occurrences. "
        
        return speech
    
    def read_full_report(self):
        """Read a comprehensive full report aloud"""
        speech = "Let me give you a comprehensive activity report. "
        
        # Daily summary
        speech += "First, today's summary: "
        daily = self.activity.get_daily_summary()
        if 'message' not in daily:
            speech += self._format_daily_summary_for_speech(daily)
        
        # Habits
        speech += "Next, your learned habits: "
        habits = self.activity.get_habits()
        speech += self._format_habits_for_speech(habits)
        
        # Productivity
        speech += "Finally, your productivity metrics: "
        report = self.activity.get_productivity_report("daily")
        speech += self._format_productivity_report_for_speech(report, "daily")
        
        if self.voice:
            self.voice.speak(speech)
        
        return speech


# ============================================================
# INTEGRATION WITH COMMANDPROCESSOR
# ============================================================

def create_voice_report_reader(voice_handler, activity_integration):
    """Factory function to create voice report reader"""
    return VoiceReportReader(voice_handler, activity_integration)
