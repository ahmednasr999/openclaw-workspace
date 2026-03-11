#!/usr/bin/env python3
"""
Enhanced Response Tracker
========================
Advanced metrics, time-series analysis, and competitive intelligence.

Usage:
    python3 response_tracker_enhanced.py --dashboard    # Full dashboard
    python3 response_tracker_enhanced.py --trend        # Trend analysis
    python3 response_tracker_enhanced.py --companies   # Company analysis
    python3 response_tracker_enhanced.py --forecast     # Pipeline forecast
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

CONFIG = {
    "workspace": "/root/.openclaw/workspace",
    "history_file": "/root/.openclaw/workspace/.response_history.json",
    "pipeline_file": "/root/.openclaw/workspace/.pipeline_forecast.json"
}

class EnhancedResponseTracker:
    def __init__(self):
        self.workspace = Path(CONFIG["workspace"])
        self.history_file = self.workspace / CONFIG["history_file"]
        self.pipeline_file = self.workspace / CONFIG["pipeline_file"]
        self.history = self.load_history()
    
    def load_history(self):
        if self.history_file.exists():
            with open(self.history_file) as f:
                return json.load(f)
        return {
            "applications": [],
            "responses": [],
            "interviews": [],
            "offers": [],
            "touchpoints": [],
            "notes": []
        }
    
    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def record_application(self, company, role, salary, source="Direct", date=None):
        """Record a new application"""
        app = {
            "id": len(self.history["applications"]) + 1,
            "company": company,
            "role": role,
            "salary": salary,
            "source": source,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "responded": False,
            "interview": False,
            "offer": False,
            "rejected": False,
            "response_time": None,
            "interview_time": None,
            "offer_time": None
        }
        self.history["applications"].append(app)
        self.save_history()
        return app
    
    def record_response(self, company, date=None, response_type="generic"):
        """Record a response"""
        self.history["responses"].append({
            "company": company,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "type": response_type  # call, email, rejection
        })
        
        # Update application
        for app in self.history["applications"]:
            if app["company"] == company and not app["responded"]:
                app["responded"] = True
                if date:
                    app["response_time"] = date
                else:
                    app["response_time"] = datetime.now().strftime("%Y-%m-%d")
        
        self.save_history()
    
    def record_interview(self, company, date=None, round_num=1):
        """Record an interview"""
        self.history["interviews"].append({
            "company": company,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "round": round_num
        })
        
        # Update application
        for app in self.history["applications"]:
            if app["company"] == company:
                app["interview"] = True
                if date:
                    app["interview_time"] = date
                else:
                    app["interview_time"] = datetime.now().strftime("%Y-%m-%d")
        
        self.save_history()
    
    def record_offer(self, company, salary, date=None):
        """Record an offer"""
        self.history["offers"].append({
            "company": company,
            "salary": salary,
            "date": date or datetime.now().strftime("%Y-%m-%d")
        })
        
        # Update application
        for app in self.history["applications"]:
            if app["company"] == company:
                app["offer"] = True
                if date:
                    app["offer_time"] = date
                else:
                    app["offer_time"] = datetime.now().strftime("%Y-%m-%d")
        
        self.save_history()
    
    def record_touchpoint(self, company, touch_type, notes=""):
        """Record a touchpoint (call, email, meeting)"""
        self.history["touchpoints"].append({
            "company": company,
            "type": touch_type,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "notes": notes
        })
        self.save_history()
    
    # === CALCULATIONS ===
    def calculate_metrics(self):
        """Calculate all metrics"""
        apps = self.history["applications"]
        total = len(apps)
        
        if total == 0:
            return None
        
        responded = [a for a in apps if a["responded"]]
        interviewed = [a for a in apps if a["interview"]]
        offered = [a for a in apps if a["offer"]]
        rejected = [a for a in apps if a["rejected"]]
        
        # Response rates
        response_rate = len(responded) / total * 100 if total > 0 else 0
        interview_rate = len(interviewed) / total * 100 if total > 0 else 0
        offer_rate = len(offered) / total * 100 if total > 0 else 0
        rejection_rate = len(rejected) / total * 100 if total > 0 else 0
        
        # Conversion rates
        resp_to_interview = len(interviewed) / len(responded) * 100 if responded else 0
        interview_to_offer = len(offered) / len(interviewed) * 100 if interviewed else 0
        
        # Time metrics
        response_times = self.calculate_response_times()
        interview_times = self.calculate_interview_times()
        offer_times = self.calculate_offer_times()
        
        # Salary metrics
        salaries = [a["salary"] for a in apps if a["salary"] > 0]
        avg_salary = mean(salaries) if salaries else 0
        offer_salaries = [o["salary"] for o in self.history["offers"]]
        avg_offer = mean(offer_salaries) if offer_salaries else 0
        
        return {
            "total_applications": total,
            "response_count": len(responded),
            "interview_count": len(interviewed),
            "offer_count": len(offered),
            "rejection_count": len(rejected),
            "response_rate": response_rate,
            "interview_rate": interview_rate,
            "offer_rate": offer_rate,
            "rejection_rate": rejection_rate,
            "resp_to_interview": resp_to_interview,
            "interview_to_offer": interview_to_offer,
            "response_times": response_times,
            "interview_times": interview_times,
            "offer_times": offer_times,
            "avg_salary": avg_salary,
            "avg_offer": avg_offer,
            "total_responses": len(self.history["responses"]),
            "total_touchpoints": len(self.history["touchpoints"])
        }
    
    def calculate_response_times(self):
        """Calculate response time in days"""
        times = []
        for app in self.history["applications"]:
            if app["responded"] and app["response_time"]:
                try:
                    app_date = datetime.strptime(app["date"], "%Y-%m-%d")
                    resp_date = datetime.strptime(app["response_time"], "%Y-%m-%d")
                    times.append((resp_date - app_date).days)
                except:
                    pass
        return times
    
    def calculate_interview_times(self):
        """Calculate time to interview in days"""
        times = []
        for app in self.history["applications"]:
            if app["interview"] and app["interview_time"]:
                try:
                    app_date = datetime.strptime(app["date"], "%Y-%m-%d")
                    int_date = datetime.strptime(app["interview_time"], "%Y-%m-%d")
                    times.append((int_date - app_date).days)
                except:
                    pass
        return times
    
    def calculate_offer_times(self):
        """Calculate time to offer in days"""
        times = []
        for app in self.history["applications"]:
            if app["offer"] and app["offer_time"]:
                try:
                    app_date = datetime.strptime(app["date"], "%Y-%m-%d")
                    off_date = datetime.strptime(app["offer_time"], "%Y-%m-%d")
                    times.append((off_date - app_date).days)
                except:
                    pass
        return times
    
    def trend_analysis(self, period="week"):
        """Analyze trends over time"""
        apps = self.history["applications"]
        
        # Group by week/month
        if period == "week":
            apps_by_period = defaultdict(list)
            for app in apps:
                date = datetime.strptime(app["date"], "%Y-%m-%d")
                week_start = date - timedelta(days=date.weekday())
                apps_by_period[week_start.strftime("%Y-%W")].append(app)
        else:
            apps_by_period = defaultdict(list)
            for app in apps:
                date = datetime.strptime(app["date"], "%Y-%m-%d")
                apps_by_period[date.strftime("%Y-%m")].append(app)
        
        trends = []
        for period_key in sorted(apps_by_period.keys()):
            period_apps = apps_by_period[period_key]
            responded = [a for a in period_apps if a["responded"]]
            interviewed = [a for a in period_apps if a["interview"]]
            
            trends.append({
                "period": period_key,
                "total": len(period_apps),
                "responses": len(responded),
                "interviews": len(interviewed),
                "response_rate": len(responded) / len(period_apps) * 100 if period_apps else 0
            })
        
        return trends
    
    def company_analysis(self):
        """Detailed company analysis"""
        companies = defaultdict(lambda: {
            "applied": 0,
            "responded": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
            "salaries": [],
            "touchpoints": []
        })
        
        for app in self.history["applications"]:
            c = app["company"]
            companies[c]["applied"] += 1
            if app["responded"]:
                companies[c]["responded"] += 1
            if app["interview"]:
                companies[c]["interview"] += 1
            if app["offer"]:
                companies[c]["offer"] += 1
            if app["rejected"]:
                companies[c]["rejected"] += 1
            if app["salary"] > 0:
                companies[c]["salaries"].append(app["salary"])
        
        for tp in self.history["touchpoints"]:
            companies[tp["company"]]["touchpoints"].append(tp)
        
        return dict(companies)
    
    def pipeline_forecast(self):
        """Forecast pipeline outcomes"""
        metrics = self.calculate_metrics()
        if not metrics:
            return None
        
        # Current pipeline
        apps = self.history["applications"]
        active = [a for a in apps if not a["responded"]]
        in_progress = [a for a in apps if a["responded"] and not a["offer"] and not a["rejected"]]
        
        # Expected outcomes based on rates
        expected_responses = len(active) * (metrics["response_rate"] / 100)
        expected_interviews = expected_responses * (metrics["resp_to_interview"] / 100)
        expected_offers = expected_interviews * (metrics["interview_to_offer"] / 100)
        
        # Average salary forecast
        salaries = [a["salary"] for a in apps if a["salary"] > 0]
        avg_salary = mean(salaries) if salaries else 0
        
        # Time projections
        response_times = metrics["response_times"]
        interview_times = metrics["interview_times"]
        
        return {
            "active_pipeline": len(active),
            "in_progress": len(in_progress),
            "expected_responses": round(expected_responses, 1),
            "expected_interviews": round(expected_interviews, 1),
            "expected_offers": round(expected_offers, 1),
            "expected_salary": avg_salary,
            "avg_response_days": round(mean(response_times), 1) if response_times else None,
            "avg_interview_days": round(mean(interview_times), 1) if interview_times else None,
            "best_case_value": expected_offers * avg_salary,
            "pipeline_value": len(active) * avg_salary
        }
    
    def generate_dashboard(self):
        """Generate full dashboard"""
        metrics = self.calculate_metrics()
        if not metrics:
            print("No data yet. Start recording applications!")
            return
        
        trends = self.trend_analysis("week")
        companies = self.company_analysis()
        forecast = self.pipeline_forecast()
        
        # Get top companies
        top_companies = sorted(companies.items(), key=lambda x: -x[1]["applied"])[:5]
        
        dashboard = f"""
{'='*70}
🎯 PIPELINE DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*70}

📊 *OVERALL METRICS*
─────────────────────────────
Total Applications: {metrics['total_applications']}
Responses: {metrics['response_count']} ({metrics['response_rate']:.1f}%)
Interviews: {metrics['interview_count']} ({metrics['interview_rate']:.1f}%)
Offers: {metrics['offer_count']} ({metrics['offer_rate']:.1f}%)
Rejections: {metrics['rejection_count']} ({metrics['rejection_rate']:.1f}%)

🔄 *CONVERSION FUNNEL*
─────────────────────────────
Application → Response: {metrics['response_rate']:.1f}%
  ↓
Response → Interview: {metrics['resp_to_interview']:.1f}%
  ↓
Interview → Offer: {metrics['interview_to_offer']:.1f}%

⏱️ *TIMING (Days)*
─────────────────────────────
Avg Time to Response: {round(mean(metrics['response_times']), 1) if metrics['response_times'] else 'N/A'} days
Avg Time to Interview: {round(mean(metrics['interview_times']), 1) if metrics['interview_times'] else 'N/A'} days
Avg Time to Offer: {round(mean(metrics['offer_times']), 1) if metrics['offer_times'] else 'N/A'} days

💰 *SALARY*
─────────────────────────────
Avg Asking: ${metrics['avg_salary']:,.0f}/mo
Avg Offer: ${metrics['avg_offer']:,.0f}/mo

📈 *TOP COMPANIES*
─────────────────────────────"""
        
        for company, data in top_companies:
            dashboard += f"""
  • {company}: {data['applied']} apps, {data['interview']} interviews, {data['offer']} offers"""
        
        dashboard += f"""

🔮 *PIPELINE FORECAST*
─────────────────────────────
Active Opportunities: {forecast['active_pipeline']}
In Progress: {forecast['in_progress']}
Expected Responses: {forecast['expected_responses']:.1f}
Expected Interviews: {forecast['expected_interviews']:.1f}
Expected Offers: {forecast['expected_offers']:.1f}
Potential Value: ${forecast['best_case_value']:,.0f}/mo

📊 *WEEKLY TRENDS*
─────────────────────────────"""
        
        for trend in trends[-4:]:  # Last 4 weeks
            dashboard += f"""
  Week {trend['period']}: {trend['total']} apps, {trend['responses']} responses ({trend['response_rate']:.0f}%)"""
        
        dashboard += f"""

{'='*70}
"""
        
        print(dashboard)
        return dashboard
    
    def competitive_intelligence(self):
        """Analyze competitive position"""
        companies = self.company_analysis()
        
        if not companies:
            return None
        
        # Best response rates
        responded_companies = {c: d for c, d in companies.items() if d['responded'] > 0}
        if responded_companies:
            best_response = max(responded_companies.items(), key=lambda x: x[1]['responded'] / x[1]['applied'] * 100 if x[1]['applied'] > 0 else 0)
        
        # Most interviews
        most_interviews = max(companies.items(), key=lambda x: x[1]['interview'])
        
        # Highest salary requests
        salary_companies = {c: mean(d['salaries']) for c, d in companies.items() if d['salaries']}
        highest_salary = max(salary_companies.items(), key=lambda x: x[1]) if salary_companies else None
        
        return {
            "best_response_rate": best_response if 'best_response' in dir() else None,
            "most_interviews": most_interviews,
            "highest_salary": highest_salary,
            "total_companies": len(companies),
            "unique_companies": len(set(a['company'] for a in self.history['applications']))
        }


if __name__ == "__main__":
    import sys
    
    tracker = EnhancedResponseTracker()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--dashboard" or cmd == "-d":
            tracker.generate_dashboard()
        elif cmd == "--trend" or cmd == "-t":
            trends = tracker.trend_analysis("week")
            for t in trends:
                print(f"Week {t['period']}: {t['total']} apps, {t['response_rate']:.0f}% response rate")
        elif cmd == "--companies" or cmd == "-c":
            companies = tracker.company_analysis()
            for c, d in sorted(companies.items(), key=lambda x: -x[1]['applied']):
                print(f"{c}: {d['applied']} apps, {d['interview']} interviews, {d['offer']} offers")
        elif cmd == "--forecast" or cmd == "-f":
            forecast = tracker.pipeline_forecast()
            if forecast:
                for k, v in forecast.items():
                    print(f"{k}: {v}")
        elif cmd == "--competitive":
            intel = tracker.competitive_intelligence()
            if intel:
                print(f"Unique companies: {intel['unique_companies']}")
                print(f"Most interviews: {intel['most_interviews'][0]}: {intel['most_interviews'][1]['interview']}")
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: response_tracker_enhanced.py [--dashboard|--trend|--companies|--forecast|--competitive]")
    else:
        tracker.generate_dashboard()
