#!/usr/bin/env python3
"""
Response Rate Tracker
====================
Track application outcomes and calculate response metrics.

Usage:
    python3 response_tracker.py --report    # Show full report
    python3 response_tracker.py --trend      # Show trend over time
    python3 response_tracker.py --company   # Company-level analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path

CONFIG = {
    "workspace": "/root/.openclaw/workspace",
    "history_file": "/root/.openclaw/workspace/.response_history.json"
}

class ResponseTracker:
    def __init__(self):
        self.workspace = Path(CONFIG["workspace"])
        self.history_file = Path(CONFIG["history_file"])
        self.history = self.load_history()
    
    def load_history(self):
        if self.history_file.exists():
            with open(self.history_file) as f:
                return json.load(f)
        return {"applications": [], "responses": [], "interviews": [], "offers": []}
    
    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def record_application(self, company, role, salary, date=None):
        """Record a new application"""
        app = {
            "company": company,
            "role": role,
            "salary": salary,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "responded": False,
            "interview": False,
            "offer": False
        }
        self.history["applications"].append(app)
        self.save_history()
        return app
    
    def record_response(self, company, date=None):
        """Record a response to an application"""
        self.history["responses"].append({
            "company": company,
            "date": date or datetime.now().strftime("%Y-%m-%d")
        })
        self.save_history()
    
    def record_interview(self, company, date=None):
        """Record an interview"""
        self.history["interviews"].append({
            "company": company,
            "date": date or datetime.now().strftime("%Y-%m-%d")
        })
        self.save_history()
    
    def record_offer(self, company, salary, date=None):
        """Record an offer"""
        self.history["offers"].append({
            "company": company,
            "salary": salary,
            "date": date or datetime.now().strftime("%Y-%m-%d")
        })
        self.save_history()
    
    def calculate_rates(self):
        """Calculate response metrics"""
        apps = self.history["applications"]
        responses = self.history["responses"]
        interviews = self.history["interviews"]
        offers = self.history["offers"]
        
        total = len(apps)
        responded = len(responses)
        interview_count = len(interviews)
        offer_count = len(offers)
        
        return {
            "total_applications": total,
            "response_count": responded,
            "interview_count": interview_count,
            "offer_count": offer_count,
            "response_rate": (responded / total * 100) if total > 0 else 0,
            "interview_rate": (interview_count / total * 100) if total > 0 else 0,
            "offer_rate": (offer_count / total * 100) if total > 0 else 0,
            "response_to_interview": (interview_count / responded * 100) if responded > 0 else 0,
            "interview_to_offer": (offer_count / interview_count * 100) if interview_count > 0 else 0
        }
    
    def company_analysis(self):
        """Analyze by company"""
        companies = {}
        
        for app in self.history["applications"]:
            company = app["company"]
            if company not in companies:
                companies[company] = {
                    "applied": 0,
                    "responded": 0,
                    "interview": 0,
                    "offer": 0
                }
            companies[company]["applied"] += 1
        
        for resp in self.history["responses"]:
            company = resp["company"]
            if company in companies:
                companies[company]["responded"] += 1
        
        for interv in self.history["interviews"]:
            company = interv["company"]
            if company in companies:
                companies[company]["interview"] += 1
        
        for off in self.history["offers"]:
            company = off["company"]
            if company in companies:
                companies[company]["offer"] += 1
        
        return companies
    
    def generate_report(self):
        """Generate full report"""
        rates = self.calculate_rates()
        companies = self.company_analysis()
        
        report = f"""
{'='*60}
RESPONSE RATE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*60}

📊 *OVERALL METRICS*
─────────────────────
Total Applications: {rates['total_applications']}
Responses: {rates['response_count']} ({rates['response_rate']:.1f}%)
Interviews: {rates['interview_count']} ({rates['interview_rate']:.1f}%)
Offers: {rates['offer_count']} ({rates['offer_rate']:.1f}%)

🎯 *CONVERSION RATES*
─────────────────────
Response Rate: {rates['response_rate']:.1f}%
Response → Interview: {rates['response_to_interview']:.1f}%
Interview → Offer: {rates['interview_to_offer']:.1f}%

💰 *AVERAGE OFFERS*
───────────────────
"""
        
        for off in self.history["offers"]:
            report += f"  • {off['company']}: ${off['salary']:,}/mo\n"
        
        report += f"""
🏢 *COMPANY BREAKDOWN*
─────────────────────
"""
        
        for company, data in sorted(companies.items(), key=lambda x: -x[1]['applied']):
            report += f"""
{company}:
  Applied: {data['applied']}
  Responded: {data['responded']}
  Interview: {data['interview']}
  Offer: {data['offer']}
"""
        
        report += """
{'='*60}
"""
        
        return report
    
    def print_report(self):
        """Print the report"""
        print(self.generate_report())


if __name__ == "__main__":
    import sys
    
    tracker = ResponseTracker()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--report":
            tracker.print_report()
        elif cmd == "--trend":
            # Show trend over time
            print("Trend analysis not yet implemented")
        elif cmd == "--company":
            companies = tracker.company_analysis()
            for company, data in sorted(companies.items()):
                print(f"{company}: {data}")
        else:
            print("Usage: response_tracker.py [--report|--trend|--company]")
    else:
        tracker.print_report()
