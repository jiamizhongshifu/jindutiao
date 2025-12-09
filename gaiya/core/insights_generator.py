"""
Weekly Insights Generator - Personal productivity analysis

Generates personalized weekly reports with:
- Productivity trends
- Top time-consuming apps
- Focus time analysis
- Improvement suggestions

Author: GaiYa Team
Date: 2025-12-09
Version: 1.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from collections import defaultdict


class InsightsGenerator:
    """
    Weekly Insights Generator

    Analyzes user behavior and generates actionable insights:
    1. Productivity trend (improving/declining)
    2. Top 3 time-consuming applications
    3. Best focus hours identification
    4. Personalized improvement suggestions
    """

    def __init__(self, stats_manager, logger: Optional[logging.Logger] = None):
        """
        Initialize Insights Generator

        Args:
            stats_manager: StatisticsManager instance
            logger: Logger instance
        """
        self.stats_manager = stats_manager
        self.logger = logger or logging.getLogger(__name__)

    def generate_weekly_insights(self, days: int = 7) -> Dict[str, any]:
        """
        Generate comprehensive weekly insights

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with insights:
            {
                'period': str,                    # Analysis period
                'productivity_trend': dict,       # Trend analysis
                'top_apps': List[dict],          # Top time-consuming apps
                'focus_analysis': dict,          # Focus hours analysis
                'suggestions': List[str],        # Improvement suggestions
                'summary': str                   # Overall summary
            }
        """
        self.logger.info(f"Generating weekly insights for last {days} days...")

        # Get data
        trend_data = self.stats_manager.get_weekly_trend(days=days)
        category_data = self.stats_manager.get_category_distribution(days=days)

        # Analysis period
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        period_str = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

        # 1. Productivity Trend Analysis
        productivity_trend = self._analyze_productivity_trend(trend_data)

        # 2. Top Time-Consuming Categories
        top_apps = self._get_top_categories(category_data, top_n=3)

        # 3. Focus Time Analysis
        focus_analysis = self._analyze_focus_patterns(trend_data)

        # 4. Personalized Suggestions
        suggestions = self._generate_suggestions(
            productivity_trend,
            category_data,
            focus_analysis
        )

        # 5. Overall Summary
        summary = self._generate_summary(
            productivity_trend,
            top_apps,
            focus_analysis
        )

        insights = {
            'period': period_str,
            'productivity_trend': productivity_trend,
            'top_apps': top_apps,
            'focus_analysis': focus_analysis,
            'suggestions': suggestions,
            'summary': summary,
            'generated_at': datetime.now().isoformat()
        }

        self.logger.info("Weekly insights generated successfully")
        return insights

    def _analyze_productivity_trend(self, trend_data: List[Dict]) -> Dict[str, any]:
        """
        Analyze productivity trend (improving/declining/stable)

        Args:
            trend_data: Weekly trend data

        Returns:
            Trend analysis dict
        """
        if not trend_data or len(trend_data) < 2:
            return {
                'status': 'insufficient_data',
                'description': '数据不足,无法分析趋势',
                'emoji': '⚠️',
                'change': 0.0
            }

        # Calculate average completion rate for first half and second half
        mid_point = len(trend_data) // 2
        first_half = trend_data[:mid_point]
        second_half = trend_data[mid_point:]

        first_avg = sum(d['completion_rate'] for d in first_half) / len(first_half) if first_half else 0
        second_avg = sum(d['completion_rate'] for d in second_half) / len(second_half) if second_half else 0

        change = second_avg - first_avg

        # Determine trend status
        if abs(change) < 5:  # Less than 5% change
            status = 'stable'
            description = f'保持稳定 (完成率维持在 {second_avg:.1f}% 左右)'
            emoji = '➡️'
        elif change > 0:  # Improving
            status = 'improving'
            description = f'稳步提升 (完成率从 {first_avg:.1f}% 提升到 {second_avg:.1f}%)'
            emoji = '📈'
        else:  # Declining
            status = 'declining'
            description = f'有所下降 (完成率从 {first_avg:.1f}% 降至 {second_avg:.1f}%)'
            emoji = '📉'

        return {
            'status': status,
            'description': description,
            'emoji': emoji,
            'change': change,
            'first_half_avg': first_avg,
            'second_half_avg': second_avg
        }

    def _get_top_categories(self, category_data: Dict[str, Dict], top_n: int = 3) -> List[Dict]:
        """
        Get top N time-consuming task categories

        Args:
            category_data: Category distribution data
            top_n: Number of top categories to return

        Returns:
            List of top categories with stats
        """
        if not category_data:
            return []

        # Sort by total minutes (descending)
        sorted_categories = sorted(
            category_data.items(),
            key=lambda x: x[1]['total_minutes'],
            reverse=True
        )

        # Calculate total minutes for percentage
        total_minutes = sum(cat['total_minutes'] for cat in category_data.values())

        # Build result
        top_categories = []
        category_emoji = {
            '工作': '🏢',
            '学习': '📚',
            '运动': '🏃',
            '饮食': '🍽️',
            '休息': '😴',
            '娱乐': '🎮',
            '通勤': '🚗',
            '其他': '🔧'
        }

        for i, (category_name, stats) in enumerate(sorted_categories[:top_n], 1):
            minutes = stats['total_minutes']
            hours = minutes / 60
            percentage = (minutes / total_minutes * 100) if total_minutes > 0 else 0
            emoji = category_emoji.get(category_name, '📌')

            top_categories.append({
                'rank': i,
                'category': category_name,
                'emoji': emoji,
                'total_minutes': minutes,
                'hours': round(hours, 1),
                'percentage': round(percentage, 1),
                'task_count': stats['count'],
                'completed_count': stats['completed']
            })

        return top_categories

    def _analyze_focus_patterns(self, trend_data: List[Dict]) -> Dict[str, any]:
        """
        Analyze focus time patterns

        Args:
            trend_data: Weekly trend data

        Returns:
            Focus analysis dict
        """
        if not trend_data:
            return {
                'best_days': [],
                'avg_completion_rate': 0.0,
                'total_tasks': 0,
                'completed_tasks': 0
            }

        # Find best performing days
        sorted_days = sorted(
            trend_data,
            key=lambda x: x['completion_rate'],
            reverse=True
        )

        best_days = []
        for day in sorted_days[:3]:  # Top 3 days
            day_of_week = datetime.strptime(day['date'], '%Y-%m-%d').strftime('%A')
            day_of_week_cn = {
                'Monday': '周一',
                'Tuesday': '周二',
                'Wednesday': '周三',
                'Thursday': '周四',
                'Friday': '周五',
                'Saturday': '周六',
                'Sunday': '周日'
            }.get(day_of_week, day_of_week)

            best_days.append({
                'date': day['date'],
                'day_of_week': day_of_week_cn,
                'completion_rate': day['completion_rate'],
                'total_tasks': day['total_tasks'],
                'completed_tasks': day['completed_tasks']
            })

        # Overall stats
        total_tasks = sum(d['total_tasks'] for d in trend_data)
        completed_tasks = sum(d['completed_tasks'] for d in trend_data)
        avg_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            'best_days': best_days,
            'avg_completion_rate': round(avg_completion_rate, 1),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        }

    def _generate_suggestions(
        self,
        productivity_trend: Dict,
        category_data: Dict[str, Dict],
        focus_analysis: Dict
    ) -> List[str]:
        """
        Generate personalized improvement suggestions

        Args:
            productivity_trend: Productivity trend analysis
            category_data: Category distribution data
            focus_analysis: Focus time analysis

        Returns:
            List of suggestion strings
        """
        suggestions = []

        # 1. Trend-based suggestions
        trend_status = productivity_trend.get('status')
        if trend_status == 'declining':
            suggestions.append("📉 本周完成率有所下降,建议重新审视任务优先级,聚焦最重要的事项")
        elif trend_status == 'improving':
            suggestions.append("🎉 本周表现出色!保持当前节奏,继续优化时间管理策略")
        elif trend_status == 'stable':
            suggestions.append("💪 完成率保持稳定,可以尝试挑战更高的目标")

        # 2. Category-based suggestions
        if category_data:
            # Check娱乐/休息 proportion
            entertainment_mins = category_data.get('娱乐', {}).get('total_minutes', 0)
            rest_mins = category_data.get('休息', {}).get('total_minutes', 0)
            work_mins = category_data.get('工作', {}).get('total_minutes', 0)
            study_mins = category_data.get('学习', {}).get('total_minutes', 0)

            total_productive = work_mins + study_mins
            total_non_productive = entertainment_mins + rest_mins

            if total_productive > 0 and total_non_productive / total_productive > 1.5:
                suggestions.append("⚖️ 娱乐/休息时间占比较高,建议增加学习或工作投入时间")
            elif total_productive > 0 and total_non_productive / total_productive < 0.3:
                suggestions.append("🧘 工作/学习时间较多,记得适当休息,保持身心平衡")

        # 3. Focus-based suggestions
        avg_rate = focus_analysis.get('avg_completion_rate', 0)
        if avg_rate < 60:
            suggestions.append("🎯 平均完成率较低,建议减少任务数量或延长任务时间,制定更实际的计划")
        elif avg_rate > 85:
            suggestions.append("🚀 任务完成率很高!可以尝试设置更具挑战性的目标")

        # 4. Best days insights
        best_days = focus_analysis.get('best_days', [])
        if best_days:
            best_day = best_days[0]
            suggestions.append(
                f"⭐ {best_day['day_of_week']}是你表现最好的一天"
                f"(完成率{best_day['completion_rate']:.0f}%),尝试在这天安排重要任务"
            )

        # Limit to 5 suggestions
        return suggestions[:5]

    def _generate_summary(
        self,
        productivity_trend: Dict,
        top_apps: List[Dict],
        focus_analysis: Dict
    ) -> str:
        """
        Generate overall summary text

        Args:
            productivity_trend: Productivity trend analysis
            top_apps: Top time-consuming apps
            focus_analysis: Focus time analysis

        Returns:
            Summary string
        """
        trend_emoji = productivity_trend.get('emoji', '📊')
        trend_desc = productivity_trend.get('description', '数据不足')

        avg_rate = focus_analysis.get('avg_completion_rate', 0)
        total_tasks = focus_analysis.get('total_tasks', 0)
        completed_tasks = focus_analysis.get('completed_tasks', 0)

        summary_parts = [
            f"{trend_emoji} 生产力趋势: {trend_desc}",
            f"",
            f"📋 任务统计: 共完成 {completed_tasks}/{total_tasks} 个任务 (平均完成率 {avg_rate:.1f}%)",
        ]

        if top_apps:
            top_app_names = ', '.join([f"{app['emoji']} {app['category']}" for app in top_apps[:3]])
            summary_parts.append(f"")
            summary_parts.append(f"⏱️ 主要时间投入: {top_app_names}")

        return "\n".join(summary_parts)

    def format_for_display(self, insights: Dict) -> str:
        """
        Format insights for text display

        Args:
            insights: Insights dictionary

        Returns:
            Formatted string
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append(f"📊 本周洞察报告 ({insights['period']})")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(insights['summary'])
        lines.append("")

        # Top Apps
        if insights['top_apps']:
            lines.append("🏆 时间消耗TOP 3:")
            for app in insights['top_apps']:
                lines.append(
                    f"   {app['rank']}. {app['emoji']} {app['category']} - "
                    f"{app['hours']}小时 ({app['percentage']:.1f}%)"
                )
            lines.append("")

        # Best Days
        best_days = insights['focus_analysis'].get('best_days', [])
        if best_days:
            lines.append("⭐ 表现最佳的日子:")
            for day in best_days[:3]:
                lines.append(
                    f"   • {day['date']} ({day['day_of_week']}) - "
                    f"完成率 {day['completion_rate']:.0f}%"
                )
            lines.append("")

        # Suggestions
        if insights['suggestions']:
            lines.append("💡 改进建议:")
            for i, suggestion in enumerate(insights['suggestions'], 1):
                lines.append(f"   {i}. {suggestion}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
