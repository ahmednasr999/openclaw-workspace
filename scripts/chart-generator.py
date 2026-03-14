#!/usr/bin/env python3
"""
Chart Generator for OpenClaw
Generates PNG charts for dashboards, briefings, and insights.
Usage: python3 scripts/chart-generator.py --type health
"""

import argparse
import os
import sys
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

OUTPUT_DIR = "/root/.openclaw/workspace/media"


def generate_health_chart(data):
    """Health score over time."""
    dates = data.get("dates", [])
    scores = data.get("scores", [])
    
    if not dates:
        dates = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"]
        scores = [85, 90, 88, 95, 98]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    ax.plot(dates, scores, 'o-', linewidth=3, markersize=10, color='#4ade80')
    ax.fill_between(dates, scores, alpha=0.3, color='#4ade80')
    
    ax.set_xlabel('Date', color='white')
    ax.set_ylabel('Health Score', color='white')
    ax.set_title('System Health Over Time', color='white', fontsize=14)
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    return fig


def generate_pipeline_chart(data):
    """Job pipeline stages."""
    stages = data.get("stages", ["CV Ready", "Applied", "Interview", "Offer"])
    counts = data.get("counts", [5, 12, 3, 1])
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    colors = ['#4ade80', '#60a5fa', '#f59e0b', '#ef4444']
    bars = ax.bar(stages, counts, color=colors)
    
    ax.set_xlabel('Pipeline Stage', color='white')
    ax.set_ylabel('Count', color='white')
    ax.set_title('Job Pipeline Overview', color='white', fontsize=14)
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                str(count), ha='center', color='white', fontsize=12)
    
    plt.tight_layout()
    return fig


def generate_jobs_chart(data):
    """Applications over time."""
    dates = data.get("dates", [])
    counts = data.get("counts", [])
    
    if not dates:
        dates = ["Week 1", "Week 2", "Week 3", "Week 4"]
        counts = [8, 12, 15, 10]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    ax.bar(dates, counts, color='#8b5cf6')
    
    ax.set_xlabel('Week', color='white')
    ax.set_ylabel('Applications', color='white')
    ax.set_title('Job Applications Trend', color='white', fontsize=14)
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    return fig


def generate_sessions_chart(data):
    """Session activity."""
    hours = list(range(24))
    sessions = data.get("sessions", [5, 3, 1, 0, 0, 2, 8, 15, 25, 30, 28, 22, 18, 20, 25, 30, 35, 40, 38, 25, 15, 10, 8, 5])
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    ax.fill_between(hours, sessions, alpha=0.5, color='#f472b6')
    ax.plot(hours, sessions, 'o-', linewidth=2, color='#f472b6')
    
    ax.set_xlabel('Hour of Day', color='white')
    ax.set_ylabel('Sessions', color='white')
    ax.set_title('Session Activity (24h)', color='white', fontsize=14)
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 23)
    
    plt.tight_layout()
    return fig


def generate_models_chart(data):
    """Model usage distribution."""
    models = data.get("models", ["MiniMax", "Sonnet", "Opus", "GPT-5.4", "Haiku"])
    usage = data.get("usage", [45, 25, 15, 10, 5])
    
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    colors = ['#34d399', '#60a5fa', '#a78bfa', '#f97316', '#9ca3af']
    explode = [0.05] * len(models)
    
    wedges, texts, autotexts = ax.pie(usage, labels=models, autopct='%1.1f%%',
                                       colors=colors, explode=explode,
                                       textprops={'color': 'white'})
    
    ax.set_title('Model Usage Distribution', color='white', fontsize=14)
    
    plt.tight_layout()
    return fig


# Chart type mapping
CHARTS = {
    "health": generate_health_chart,
    "pipeline": generate_pipeline_chart,
    "jobs": generate_jobs_chart,
    "sessions": generate_sessions_chart,
    "models": generate_models_chart,
}


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Chart Generator")
    parser.add_argument("--type", "-t", choices=list(CHARTS.keys()), default="health",
                       help="Chart type to generate")
    parser.add_argument("--data", "-d", default="{}", help="JSON data for chart")
    parser.add_argument("--output", "-o", help="Output file (default: auto)")
    parser.add_argument("--show", action="store_true", help="Display chart")
    args = parser.parse_args()
    
    try:
        chart_data = json.loads(args.data)
    except:
        chart_data = {}
    
    chart_func = CHARTS.get(args.type, generate_health_chart)
    fig = chart_func(chart_data)
    
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = f"{OUTPUT_DIR}/chart-{args.type}-{timestamp}.png"
    
    fig.savefig(output_path, dpi=150, facecolor='#1a1a2e')
    print(output_path)


if __name__ == "__main__":
    main()
