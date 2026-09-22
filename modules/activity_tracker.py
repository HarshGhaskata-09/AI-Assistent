# modules/activity_tracker.py - PHASE 7: Activity Tracking System

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import sqlite3

class ActivityTracker:
    """
    Comprehensive activity tracking system for AI Assistent
    Tracks: app usage, daily summaries, habit learning, productivity reports
    """
    
    def __init__(self, db_path="data/ai_assistent.db"):
        """Initialize activity tracker"""
        self.db_path = db_path
        self.activity_file = "data/activity_tracking.json"
        self.habits_file = "data/habits.json"
        self.productivity_file = "data/productivity_reports.json"
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.activity_file), exist_ok=True)
        
        # Load or initialize tracking data
        self._load_tracking_data()
    
    def _load_tracking_data(self):
        """Load tracking data from files"""
        self.activity_data = self._load_json(self.activity_file, {})
        self.habits_data = self._load_json(self.habits_file, {})
        self.productivity_data = self._load_json(self.productivity_file, {})
    
    def _load_json(self, filepath, default):
        """Load JSON file safely"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    def _save_json(self, filepath, data):
        """Save JSON file safely"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ============================================================
    # APP USAGE TRACKING
    # ============================================================
    
    def track_app_usage(self, app_name: str, duration_seconds: int = 0, category: str = "general"):
        """Track application usage"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.activity_data:
            self.activity_data[today] = {
                'apps': {},
                'commands': {},
                'sessions': [],
                'total_active_time': 0
            }
        
        if app_name not in self.activity_data[today]['apps']:
            self.activity_data[today]['apps'][app_name] = {
                'count': 0,
                'total_duration': 0,
                'category': category,
                'last_used': None,
                'timestamps': []
            }
        
        app_data = self.activity_data[today]['apps'][app_name]
        app_data['count'] += 1
        app_data['total_duration'] += duration_seconds
        app_data['last_used'] = datetime.now().isoformat()
        app_data['timestamps'].append(datetime.now().isoformat())
        
        self._save_json(self.activity_file, self.activity_data)
        return app_data
    
    def get_app_usage_summary(self, date: str = None) -> Dict:
        """Get app usage summary for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.activity_data:
            return {}
        
        apps = self.activity_data[date].get('apps', {})
        
        summary = {
            'date': date,
            'total_apps_used': len(apps),
            'apps': {},
            'by_category': defaultdict(list)
        }
        
        for app_name, app_info in apps.items():
            summary['apps'][app_name] = {
                'launches': app_info['count'],
                'total_time_seconds': app_info['total_duration'],
                'total_time_minutes': round(app_info['total_duration'] / 60, 2),
                'category': app_info['category'],
                'last_used': app_info['last_used']
            }
            
            category = app_info['category']
            summary['by_category'][category].append({
                'app': app_name,
                'launches': app_info['count'],
                'time_minutes': round(app_info['total_duration'] / 60, 2)
            })
        
        return summary
    
    def get_most_used_apps(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get most used apps in last N days"""
        app_stats = defaultdict(lambda: {'count': 0, 'duration': 0, 'category': 'general'})
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self.activity_data:
                for app_name, app_info in self.activity_data[date].get('apps', {}).items():
                    app_stats[app_name]['count'] += app_info['count']
                    app_stats[app_name]['duration'] += app_info['total_duration']
                    app_stats[app_name]['category'] = app_info['category']
        
        sorted_apps = sorted(
            app_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:limit]
        
        return [
            {
                'app': app_name,
                'launches': stats['count'],
                'total_time_minutes': round(stats['duration'] / 60, 2),
                'category': stats['category']
            }
            for app_name, stats in sorted_apps
        ]
    
    # ============================================================
    # COMMAND USAGE TRACKING
    # ============================================================
    
    def track_command_usage(self, command_type: str, success: bool = True, processing_time_ms: int = 0):
        """Track command usage"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.activity_data:
            self.activity_data[today] = {
                'apps': {},
                'commands': {},
                'sessions': [],
                'total_active_time': 0
            }
        
        if command_type not in self.activity_data[today]['commands']:
            self.activity_data[today]['commands'][command_type] = {
                'count': 0,
                'successful': 0,
                'failed': 0,
                'avg_time_ms': 0,
                'times': []
            }
        
        cmd_data = self.activity_data[today]['commands'][command_type]
        cmd_data['count'] += 1
        if success:
            cmd_data['successful'] += 1
        else:
            cmd_data['failed'] += 1
        
        cmd_data['times'].append(processing_time_ms)
        cmd_data['avg_time_ms'] = sum(cmd_data['times']) / len(cmd_data['times'])
        
        self._save_json(self.activity_file, self.activity_data)
        return cmd_data
    
    def get_command_usage_summary(self, date: str = None) -> Dict:
        """Get command usage summary"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.activity_data:
            return {}
        
        commands = self.activity_data[date].get('commands', {})
        
        summary = {
            'date': date,
            'total_commands': sum(c['count'] for c in commands.values()),
            'successful_commands': sum(c['successful'] for c in commands.values()),
            'failed_commands': sum(c['failed'] for c in commands.values()),
            'success_rate': 0,
            'commands': {}
        }
        
        if summary['total_commands'] > 0:
            summary['success_rate'] = round(
                (summary['successful_commands'] / summary['total_commands']) * 100, 2
            )
        
        for cmd_type, cmd_info in commands.items():
            summary['commands'][cmd_type] = {
                'count': cmd_info['count'],
                'successful': cmd_info['successful'],
                'failed': cmd_info['failed'],
                'success_rate': round((cmd_info['successful'] / cmd_info['count'] * 100), 2) if cmd_info['count'] > 0 else 0,
                'avg_time_ms': round(cmd_info['avg_time_ms'], 2)
            }
        
        return summary
    
    # ============================================================
    # DAILY SUMMARIES
    # ============================================================
    
    def generate_daily_summary(self, date: str = None) -> Dict:
        """Generate comprehensive daily summary"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.activity_data:
            return {'date': date, 'message': 'No activity recorded'}
        
        day_data = self.activity_data[date]
        
        # Get stats from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get daily stats
            cursor.execute('''
                SELECT total_commands, successful_commands, avg_response_time_ms
                FROM daily_stats WHERE date = ?
            ''', (date,))
            db_stats = cursor.fetchone()
            
            # Get command breakdown
            cursor.execute('''
                SELECT command_type, COUNT(*) as count, 
                       SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successful
                FROM interactions WHERE date(timestamp) = ?
                GROUP BY command_type
            ''', (date,))
            command_breakdown = cursor.fetchall()
        
        summary = {
            'date': date,
            'day_of_week': datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
            'apps_used': len(day_data.get('apps', {})),
            'total_app_launches': sum(app['count'] for app in day_data.get('apps', {}).values()),
            'total_commands': db_stats[0] if db_stats else 0,
            'successful_commands': db_stats[1] if db_stats else 0,
            'success_rate': round((db_stats[1] / db_stats[0] * 100), 2) if db_stats and db_stats[0] > 0 else 0,
            'avg_response_time_ms': db_stats[2] if db_stats else 0,
            'top_apps': self._get_top_items(day_data.get('apps', {}), 3),
            'top_commands': self._get_top_commands(command_breakdown, 3),
            'activity_level': self._calculate_activity_level(db_stats[0] if db_stats else 0),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def _get_top_items(self, items_dict: Dict, limit: int = 3) -> List[Dict]:
        """Get top items by count"""
        sorted_items = sorted(
            items_dict.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:limit]
        
        return [
            {'name': name, 'count': info['count']}
            for name, info in sorted_items
        ]
    
    def _get_top_commands(self, command_breakdown: List, limit: int = 3) -> List[Dict]:
        """Get top commands from database query"""
        sorted_commands = sorted(
            command_breakdown,
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {
                'command': cmd[0],
                'count': cmd[1],
                'successful': cmd[2]
            }
            for cmd in sorted_commands
        ]
    
    def _calculate_activity_level(self, command_count: int) -> str:
        """Calculate activity level based on command count"""
        if command_count == 0:
            return "Idle"
        elif command_count < 5:
            return "Low"
        elif command_count < 15:
            return "Moderate"
        elif command_count < 30:
            return "High"
        else:
            return "Very High"
    
    def get_weekly_summary(self) -> Dict:
        """Get weekly activity summary"""
        summaries = []
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            summary = self.generate_daily_summary(date)
            if 'message' not in summary:
                summaries.append(summary)
        
        total_commands = sum(s.get('total_commands', 0) for s in summaries)
        total_apps = sum(s.get('apps_used', 0) for s in summaries)
        avg_success_rate = sum(s.get('success_rate', 0) for s in summaries) / len(summaries) if summaries else 0
        
        return {
            'week_start': (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
            'week_end': datetime.now().strftime("%Y-%m-%d"),
            'total_commands': total_commands,
            'total_apps_used': total_apps,
            'avg_success_rate': round(avg_success_rate, 2),
            'daily_summaries': summaries,
            'most_active_day': max(summaries, key=lambda x: x.get('total_commands', 0)) if summaries else None
        }
    
    # ============================================================
    # HABIT LEARNING
    # ============================================================
    
    def learn_habit(self, habit_name: str, command_type: str, frequency: int = 1):
        """Learn user habits from repeated commands"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if habit_name not in self.habits_data:
            self.habits_data[habit_name] = {
                'command_type': command_type,
                'first_detected': today,
                'occurrences': 0,
                'last_occurrence': None,
                'pattern': [],
                'confidence': 0.0,
                'status': 'learning'
            }
        
        habit = self.habits_data[habit_name]
        habit['occurrences'] += frequency
        habit['last_occurrence'] = datetime.now().isoformat()
        habit['pattern'].append(today)
        
        # Calculate confidence (0-1 scale)
        # More occurrences = higher confidence
        habit['confidence'] = min(habit['occurrences'] / 10, 1.0)
        
        # Determine status
        if habit['occurrences'] >= 5:
            habit['status'] = 'established'
        elif habit['occurrences'] >= 3:
            habit['status'] = 'forming'
        else:
            habit['status'] = 'learning'
        
        self._save_json(self.habits_file, self.habits_data)
        return habit
    
    def get_habits(self, min_confidence: float = 0.3) -> List[Dict]:
        """Get learned habits above confidence threshold"""
        habits = []
        
        for habit_name, habit_info in self.habits_data.items():
            if habit_info['confidence'] >= min_confidence:
                habits.append({
                    'name': habit_name,
                    'command_type': habit_info['command_type'],
                    'occurrences': habit_info['occurrences'],
                    'confidence': round(habit_info['confidence'], 2),
                    'status': habit_info['status'],
                    'last_occurrence': habit_info['last_occurrence'],
                    'days_active': len(set(habit_info['pattern']))
                })
        
        return sorted(habits, key=lambda x: x['confidence'], reverse=True)
    
    def predict_next_action(self) -> Optional[Dict]:
        """Predict user's next likely action based on habits"""
        established_habits = [h for h in self.get_habits() if h['status'] == 'established']
        
        if not established_habits:
            return None
        
        # Get most confident habit
        top_habit = max(established_habits, key=lambda x: x['confidence'])
        
        return {
            'predicted_action': top_habit['name'],
            'command_type': top_habit['command_type'],
            'confidence': top_habit['confidence'],
            'based_on_occurrences': top_habit['occurrences']
        }
    
    # ============================================================
    # PRODUCTIVITY REPORTS
    # ============================================================
    
    def generate_productivity_report(self, period: str = "daily") -> Dict:
        """Generate productivity report"""
        if period == "daily":
            return self._generate_daily_productivity_report()
        elif period == "weekly":
            return self._generate_weekly_productivity_report()
        elif period == "monthly":
            return self._generate_monthly_productivity_report()
        else:
            return {}
    
    def _generate_daily_productivity_report(self) -> Dict:
        """Generate daily productivity report"""
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self.generate_daily_summary(today)
        
        report = {
            'period': 'daily',
            'date': today,
            'metrics': {
                'total_commands': summary.get('total_commands', 0),
                'success_rate': summary.get('success_rate', 0),
                'avg_response_time_ms': summary.get('avg_response_time_ms', 0),
                'apps_used': summary.get('apps_used', 0),
                'activity_level': summary.get('activity_level', 'Idle')
            },
            'insights': self._generate_insights(summary),
            'recommendations': self._generate_recommendations(summary),
            'timestamp': datetime.now().isoformat()
        }
        
        self.productivity_data[today] = report
        self._save_json(self.productivity_file, self.productivity_data)
        
        return report
    
    def _generate_weekly_productivity_report(self) -> Dict:
        """Generate weekly productivity report"""
        week_summary = self.get_weekly_summary()
        
        report = {
            'period': 'weekly',
            'week_start': week_summary['week_start'],
            'week_end': week_summary['week_end'],
            'metrics': {
                'total_commands': week_summary['total_commands'],
                'avg_success_rate': week_summary['avg_success_rate'],
                'total_apps_used': week_summary['total_apps_used'],
                'most_active_day': week_summary['most_active_day']['day_of_week'] if week_summary['most_active_day'] else None
            },
            'daily_breakdown': [
                {
                    'date': s['date'],
                    'commands': s['total_commands'],
                    'success_rate': s['success_rate']
                }
                for s in week_summary['daily_summaries']
            ],
            'insights': self._generate_weekly_insights(week_summary),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_monthly_productivity_report(self) -> Dict:
        """Generate monthly productivity report"""
        today = datetime.now()
        month_start = today.replace(day=1)
        
        total_commands = 0
        total_success = 0
        days_active = 0
        
        for i in range((today - month_start).days + 1):
            date = (month_start + timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self.activity_data:
                days_active += 1
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT total_commands, successful_commands
                        FROM daily_stats WHERE date = ?
                    ''', (date,))
                    result = cursor.fetchone()
                    if result:
                        total_commands += result[0]
                        total_success += result[1]
        
        report = {
            'period': 'monthly',
            'month': today.strftime("%B %Y"),
            'metrics': {
                'total_commands': total_commands,
                'success_rate': round((total_success / total_commands * 100), 2) if total_commands > 0 else 0,
                'days_active': days_active,
                'avg_commands_per_day': round(total_commands / days_active, 2) if days_active > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_insights(self, summary: Dict) -> List[str]:
        """Generate insights from daily summary"""
        insights = []
        
        if summary.get('success_rate', 0) > 90:
            insights.append("Excellent command success rate today!")
        elif summary.get('success_rate', 0) < 70:
            insights.append("Consider reviewing failed commands for improvement.")
        
        if summary.get('total_commands', 0) > 20:
            insights.append("High activity level detected.")
        
        if summary.get('avg_response_time_ms', 0) > 100:
            insights.append("Response times are slower than usual.")
        
        return insights
    
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """Generate recommendations based on activity"""
        recommendations = []
        
        if summary.get('total_commands', 0) < 5:
            recommendations.append("Try using more voice commands for better productivity.")
        
        if summary.get('apps_used', 0) > 10:
            recommendations.append("Consider organizing frequently used apps into categories.")
        
        return recommendations
    
    def _generate_weekly_insights(self, week_summary: Dict) -> List[str]:
        """Generate weekly insights"""
        insights = []
        
        avg_commands = week_summary['total_commands'] / 7
        if avg_commands > 20:
            insights.append(f"Average {round(avg_commands)} commands per day - very active week!")
        
        if week_summary['avg_success_rate'] > 85:
            insights.append("Consistently high success rate this week.")
        
        return insights
    
    def get_stats(self) -> Dict:
        """Get overall activity tracker statistics"""
        return {
            'total_days_tracked': len(self.activity_data),
            'total_habits_learned': len(self.habits_data),
            'established_habits': len([h for h in self.habits_data.values() if h['status'] == 'established']),
            'productivity_reports_generated': len(self.productivity_data),
            'last_activity': max(self.activity_data.keys()) if self.activity_data else None
        }
