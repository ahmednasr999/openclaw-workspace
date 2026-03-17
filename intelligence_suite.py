#!/usr/bin/env python3
"""
OpenClaw Intelligence Suite
===========================
All 10 enhancements in one unified system.

Usage:
    python3 intelligence_suite.py jd-analyze <jd_text_or_url>    # JD Auto-Analyzer
    python3 intelligence_suite.py interview-prep <role> <company>    # Interview Prep
    python3 intelligence_suite.py salary-benchmark <role>         # Salary Intelligence
    python3 intelligence_suite.py linkedin-post <topic>          # LinkedIn Draft
    python3 intelligence_suite.py email-followup <company>       # Email Sequence
    python3 intelligence_suite.py company-research <company>    # Company Research
    python3 intelligence_suite.py interview-notes <company>     # Interview Notes DB
    python3 intelligence_suite.py skill-gap <role>              # Skill Gap Analysis
    python3 intelligence_suite.py cv-multi <role> <lang>       # Multi-language CV
    python3 intelligence_suite.py market-trends <sector>       # Market Trends

Or use: python3 intelligence_suite.py --all    # Run all analyzers on current pipeline
"""

import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Config
CONFIG = {
    "workspace": "/root/.openclaw/workspace",
    "memory_dir": "/root/.openclaw/workspace/memory",
    "cv_dir": "/root/.openclaw/workspace/cvs",
    "data_dir": "/root/.openclaw/workspace/.intelligence_data"
}

class IntelligenceSuite:
    def __init__(self):
        self.workspace = Path(CONFIG["workspace"])
        self.memory_dir = Path(CONFIG["memory_dir"])
        self.cv_dir = Path(CONFIG["cv_dir"])
        self.data_dir = Path(CONFIG["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load profile data
        self.profile = self.load_profile()
    
    def load_profile(self):
        """Load user profile data"""
        profile_file = self.data_dir / "profile.json"
        if profile_file.exists():
            with open(profile_file) as f:
                return json.load(f)
        
        # Default profile from memory
        profile = {
            "name": "Ahmed Nasr",
            "title": "Senior PMO / Program Director",
            "experience_years": 20,
            "skills": [
                "PMO Leadership", "Program Management", "Digital Transformation",
                "Data Governance", "AI/ML Programs", "Financial Services",
                "Healthcare", "FinTech", "Agile", "SAFe", "PMP", "CBAP"
            ],
            "industries": ["Financial Services", "Healthcare", "FinTech", "E-commerce"],
            "locations": ["UAE", "Saudi Arabia", "Egypt", "GCC"],
            "languages": ["Arabic", "English"],
            "certifications": ["PMP", "CBAP", "CSM", "CSPO", "Lean Six Sigma"],
            "salary_expectation": 45000,
            "preferred_roles": ["PMO Director", "Program Director", "VP Projects", "Data Leader"]
        }
        
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
        
        return profile
    
    # === 1. JD AUTO-ANALYZER ===
    def jd_analyze(self, jd_text):
        """Analyze JD and match against profile"""
        print("\n" + "="*60)
        print("🔍 JD AUTO-ANALYZER")
        print("="*60)
        
        # Extract requirements
        requirements = {
            "experience_years": self.extract_years(jd_text),
            "skills": self.extract_skills(jd_text),
            "education": self.extract_education(jd_text),
            "certifications": self.extract_certs(jd_text),
            "industry": self.extract_industry(jd_text),
            "location": self.extract_location(jd_text),
            "responsibilities": self.extract_responsibilities(jd_text)
        }
        
        # Match against profile
        match_score = self.calculate_match(requirements)
        
        # Output
        print(f"\n📊 MATCH ANALYSIS")
        print(f"  Overall Score: {match_score['overall']}/100")
        print(f"  Experience Match: {match_score['experience']}/100")
        print(f"  Skills Match: {match_score['skills']}/100")
        print(f"  Certifications Match: {match_score['certs']}/100")
        
        print(f"\n📋 REQUIREMENTS EXTRACTED:")
        print(f"  Experience: {requirements['experience_years']}+ years")
        print(f"  Skills: {', '.join(requirements['skills'][:5])}")
        print(f"  Education: {requirements['education']}")
        print(f"  Industry: {requirements['industry']}")
        
        print(f"\n✅ STRENGTHS:")
        for s in match_score['strengths']:
            print(f"  • {s}")
        
        print(f"\n⚠️ GAPS:")
        for g in match_score['gaps']:
            print(f"  • {g}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for r in match_score['recommendations']:
            print(f"  • {r}")
        
        return match_score
    
    def extract_years(self, text):
        """Extract years of experience required"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
            r'(\d+)\+?\s*years?\s*(?:in|of|with)',
            r'(\d+)\s*-\s*\d+\s*years'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 5  # Default
    
    def extract_skills(self, text):
        """Extract required skills"""
        skill_keywords = [
            "PMO", "program management", "project management", "agile", "SAFe",
            "data governance", "data quality", "metadata", "data architecture",
            "AI", "ML", "machine learning", "analytics", "BI",
            "stakeholder management", "executive reporting", "budget", "P&L",
            "risk management", "compliance", "regulatory", "GDPR", "SOX",
            "transformation", "digital", "cloud", "implementation"
        ]
        
        found = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found.append(skill)
        
        return found
    
    def extract_education(self, text):
        """Extract education requirements"""
        edu_keywords = ["Bachelor", "Master", "MBA", "PhD", "Engineering", "Computer Science"]
        
        for kw in edu_keywords:
            if kw.lower() in text.lower():
                return kw
        
        return "Bachelor's"
    
    def extract_certs(self, text):
        """Extract required certifications"""
        cert_keywords = ["PMP", "PRINCE2", "Six Sigma", "CBAP", "CSM", "CSPO", "ITIL", "MBA", "MBA"]
        
        found = []
        for cert in cert_keywords:
            if cert.lower() in text.lower():
                found.append(cert)
        
        return found
    
    def extract_industry(self, text):
        """Extract industry"""
        industries = ["Financial Services", "Banking", "FinTech", "Healthcare", "Manufacturing", "Retail", "Technology"]
        
        for ind in industries:
            if ind.lower() in text.lower():
                return ind
        
        return "Technology"
    
    def extract_location(self, text):
        """Extract location"""
        locations = ["UAE", "Dubai", "Abu Dhabi", "Saudi", "Riyadh", "Egypt", "KSA", "GCC", "Middle East"]
        
        found = []
        for loc in locations:
            if loc.lower() in text.lower():
                found.append(loc)
        
        return found[0] if found else "UAE"
    
    def extract_responsibilities(self, text):
        """Extract key responsibilities"""
        resp_keywords = [
            "lead", "manage", "oversee", "govern", "deliver", "implement",
            "design", "develop", "build", "establish", "coordinate", "strategic"
        ]
        
        found = []
        for kw in resp_keywords:
            if kw.lower() in text.lower():
                found.append(kw)
        
        return found[:5]
    
    def calculate_match(self, requirements):
        """Calculate match score"""
        score = {
            "overall": 0,
            "experience": 0,
            "skills": 0,
            "certs": 0,
            "strengths": [],
            "gaps": [],
            "recommendations": []
        }
        
        # Experience match
        req_years = requirements.get("experience_years", 5)
        profile_years = self.profile.get("experience_years", 20)
        
        if req_years <= profile_years:
            score["experience"] = 100
            score["strengths"].append(f"Experience: {profile_years} years exceeds {req_years} required")
        else:
            score["experience"] = 50
            score["gaps"].append(f"Experience: Need {req_years} years, have {profile_years}")
        
        # Skills match
        req_skills = set([s.lower() for s in requirements.get("skills", [])])
        profile_skills = set([s.lower() for s in self.profile.get("skills", [])])
        
        matched = req_skills.intersection(profile_skills)
        skill_score = int(len(matched) / max(len(req_skills), 1) * 100) if req_skills else 50
        score["skills"] = skill_score
        
        if matched:
            score["strengths"].append(f"Skills: {', '.join(list(matched)[:3])}")
        
        unmatched = req_skills - profile_skills
        if unmatched:
            score["gaps"].append(f"Missing skills: {', '.join(list(unmatched)[:3])}")
            score["recommendations"].append(f"Highlight matching skills: {', '.join(list(matched)[:3])}")
        
        # Certs match
        req_certs = set([c.lower() for c in requirements.get("certifications", [])])
        profile_certs = set([c.lower() for c in self.profile.get("certifications", [])])
        
        matched_certs = req_certs.intersection(profile_certs)
        score["certs"] = int(len(matched_certs) / max(len(req_certs), 1) * 100) if req_certs else 80
        
        if matched_certs:
            score["strengths"].append(f"Certifications: {', '.join(list(matched_certs))}")
        
        # Overall
        score["overall"] = int((score["experience"] + score["skills"] + score["certs"]) / 3)
        
        # Recommendations
        if score["overall"] >= 80:
            score["recommendations"].append("Strong match - proceed with application")
        elif score["overall"] >= 60:
            score["recommendations"].append("Good match - tailor CV to highlight matching skills")
        else:
            score["recommendations"].append("Weak match - consider if role aligns with career goals")
        
        return score
    
    # === 2. INTERVIEW PREP GENERATOR ===
    def interview_prep(self, role, company):
        """Generate interview preparation"""
        print("\n" + "="*60)
        print("🎯 INTERVIEW PREP GENERATOR")
        print("="*60)
        
        # Research company (simulated)
        company_data = self.research_company(company)
        
        # Generate likely questions
        questions = self.generate_questions(role, company_data)
        
        # Generate talking points
        talking_points = self.generate_talking_points(role, company_data)
        
        # Generate scenarios
        scenarios = self.generate_scenarios(role)
        
        print(f"\n📋 {company.upper()} - {role}")
        print(f"   Industry: {company_data['industry']}")
        print(f"   Size: {company_data['size']}")
        
        print(f"\n🎤 LIKELY QUESTIONS:")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q}")
        
        print(f"\n💬 TALKING POINTS:")
        for tp in talking_points:
            print(f"   • {tp}")
        
        print(f"\n🎬 SCENARIOS TO PREPARE:")
        for s in scenarios:
            print(f"   • {s}")
        
        return {
            "questions": questions,
            "talking_points": talking_points,
            "scenarios": scenarios
        }
    
    def research_company(self, company):
        """Simulated company research"""
        # In real implementation, this would scrape company info
        company_lower = company.lower()
        
        if any(x in company_lower for x in ["bank", "finance", "capital"]):
            industry = "Financial Services"
            size = "Large (5000+)"
        elif any(x in company_lower for x in ["hospital", "health", "medical"]):
            industry = "Healthcare"
            size = "Large (1000+)"
        elif any(x in company_lower for x in ["tech", "software", "digital"]):
            industry = "Technology"
            size = "Medium (500+)"
        else:
            industry = "Multi-industry"
            size = "Medium"
        
        return {
            "name": company,
            "industry": industry,
            "size": size,
            "region": "GCC"
        }
    
    def generate_questions(self, role, company_data):
        """Generate likely interview questions"""
        questions = [
            f"Tell me about your experience leading PMO in {company_data['industry']}",
            "Describe a time you delivered a complex program on time and budget",
            "How do you handle executive stakeholders?",
            "What's your approach to risk management?",
            "Give an example of building a team from scratch",
            "How do you prioritize competing initiatives?",
            "Describe your data governance experience",
            "How do you measure program success?"
        ]
        
        if "Financial" in company_data["industry"]:
            questions.append("How do you handle regulatory compliance in programs?")
        
        return questions
    
    def generate_talking_points(self, role, company_data):
        """Generate talking points"""
        return [
            f"Built and led PMO across 8 countries in {company_data['industry']}",
            "Delivered $50M transformation program",
            "Managed 300+ concurrent projects with 16 direct reports",
            "Experience in regulated environments (JCI, HIMSS, Visa/Mastercard)",
            "PMP, CBAP, CSM, CSPO certified"
        ]
    
    def generate_scenarios(self, role):
        """Generate scenarios to prepare for"""
        return [
            "Challenge: Program running behind schedule - how do you recover?",
            "Conflict: Executive wants to scope creep - how do you handle?",
            "Risk: Key resource leaves mid-program - how do you respond?",
            "Stakeholder: Board member disagrees with approach - how do you align?"
        ]
    
    # === 3. SALARY INTELLIGENCE ===
    def salary_benchmark(self, role):
        """Salary intelligence and benchmarks"""
        print("\n" + "="*60)
        print("💰 SALARY INTELLIGENCE")
        print("="*60)
        
        # Market data (simulated - would be from API in production)
        market_data = self.get_market_data(role)
        
        # Calculate recommendation
        recommendation = self.calculate_salary_recommendation(role, market_data)
        
        print(f"\n📊 {role.upper()}")
        print(f"   Market Range: ${market_data['min']:,} - ${market_data['max']:,}/month")
        print(f"   Median: ${market_data['median']:,}/month")
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Target: ${recommendation['target']:,}/month")
        print(f"   Range: ${recommendation['range'][0]:,} - ${recommendation['range'][1]:,}/month")
        print(f"   Rationale: {recommendation['rationale']}")
        
        if recommendation['negotiation_tips']:
            print(f"\n🎯 NEGOTIATION TIPS:")
            for tip in recommendation['negotiation_tips']:
                print(f"   • {tip}")
        
        return recommendation
    
    def get_market_data(self, role):
        """Get market salary data"""
        role_lower = role.lower()
        
        if any(x in role_lower for x in ["pmo", "program", "director", "vp"]):
            return {
                "min": 35000,
                "max": 65000,
                "median": 48000,
                "currency": "AED"
            }
        elif any(x in role_lower for x in ["data", "ai", "governance"]):
            return {
                "min": 40000,
                "max": 70000,
                "median": 52000,
                "currency": "AED"
            }
        else:
            return {
                "min": 30000,
                "max": 55000,
                "median": 42000,
                "currency": "AED"
            }
    
    def calculate_salary_recommendation(self, role, market_data):
        """Calculate salary recommendation"""
        profile_years = self.profile.get("experience_years", 20)
        profile_salary = self.profile.get("salary_expectation", 45000)
        
        # Adjust based on experience
        exp_multiplier = min(profile_years / 15, 1.3)
        
        target = int(market_data['median'] * exp_multiplier)
        
        return {
            "target": target,
            "range": (int(target * 0.9), int(target * 1.15)),
            "rationale": f"Based on {profile_years} years experience in {self.profile.get('title')}",
            "negotiation_tips": [
                "Lead with market data and your unique value",
                "Quantify impact of past programs ($50M, 300+ projects)",
                "Consider total compensation (benefits, equity)",
                "Have a BATNA (Best Alternative)"
            ]
        }
    
    # === 4. LINKEDIN AUTOMATION ===
    def linkedin_post(self, topic):
        """Generate LinkedIn post draft"""
        print("\n" + "="*60)
        print("📱 LINKEDIN POST DRAFT")
        print("="*60)
        
        # Generate post
        post = self.generate_post(topic)
        
        print(f"\n📝 DRAFT POST:")
        print(f"\n{post}\n")
        
        return post
    
    def generate_post(self, topic):
        """Generate engaging LinkedIn post"""
        hooks = [
            f"Just learned something that changed how I think about {topic}",
            f"After 20 years in program leadership, here's what I wish I knew earlier about {topic}",
            f"The biggest mistake I see with {topic} (and how to avoid it)",
            f"Hot take: {topic} is overrated unless..."
        ]
        
        body = f"""
{hooks[0]}

In my experience leading PMOs across 8 countries and managing $50M+ programs, I've found that:

• {topic} requires buy-in from the top
• Without clear governance, even the best strategy fails
• The biggest wins come from aligning incentives

What's been your experience?

#ProgramManagement #Leadership #PMO #Transformation
"""
        return body.strip()
    
    # === 5. EMAIL FOLLOW-UP ===
    def email_followup(self, company):
        """Generate email follow-up sequence"""
        print("\n" + "="*60)
        print("📧 EMAIL FOLLOW-UP SEQUENCE")
        print("="*60)
        
        sequence = [
            {
                "day": 1,
                "subject": f"Following up - {company}",
                "type": "Initial follow-up",
                "body": f"""Hi,

I wanted to follow up on my application for the PMO leadership role at {company}.

I'm particularly excited about this opportunity because of my experience leading enterprise PMOs in the GCC region and delivering large-scale transformations.

Would be happy to discuss how I can contribute to your team's success.

Best regards,
Ahmed Nasr
"""
            },
            {
                "day": 4,
                "subject": f"Quick check - {company}",
                "type": "Second follow-up",
                "body": f"""Hi,

Just checking if you had a chance to review my application for the PMO position at {company}.

I understand this is a busy time, but I'd welcome the opportunity to share more about my background and how it aligns with your needs.

Best,
Ahmed
"""
            },
            {
                "day": 7,
                "subject": f"Last check - {company}",
                "type": "Final follow-up",
                "body": f"""Hi,

I wanted to reach out one last time regarding the PMO role at {company}.

If the timing isn't right, I completely understand. I'd love to stay connected for future opportunities.

Best regards,
Ahmed
"""
            }
        ]
        
        for email in sequence:
            print(f"\n📅 Day {email['day']}: {email['type']}")
            print(f"   Subject: {email['subject']}")
            print(f"   {email['body'][:100]}...")
        
        return sequence
    
    # === 6. COMPANY RESEARCH AGENT ===
    def company_research(self, company):
        """Company research brief"""
        print("\n" + "="*60)
        print(f"🏢 COMPANY RESEARCH: {company}")
        print("="*60)
        
        research = self.gather_company_intel(company)
        
        print(f"\n📋 QUICK BRIEF:")
        print(f"   Industry: {research['industry']}")
        print(f"   Size: {research['size']}")
        print(f"   Headquarters: {research['hq']}")
        
        print(f"\n🎯 KEY TALKING POINTS:")
        for point in research['talking_points']:
            print(f"   • {point}")
        
        print(f"\n⚠️ POTENTIAL CHALLENGES:")
        for challenge in research['challenges']:
            print(f"   • {challenge}")
        
        print(f"\n💡 QUESTIONS TO ASK:")
        for q in research['questions']:
            print(f"   • {q}")
        
        return research
    
    def gather_company_intel(self, company):
        """Gather company intelligence"""
        company_lower = company.lower()
        
        if any(x in company_lower for x in ["bank", "finance"]):
            return {
                "industry": "Financial Services",
                "size": "Large",
                "hq": "UAE/Regional",
                "talking_points": [
                    "Regulatory compliance (Central Bank)",
                    "Digital transformation in banking",
                    "Risk management frameworks"
                ],
                "challenges": [
                    "Legacy systems modernization",
                    "Cybersecurity concerns",
                    "Talent acquisition"
                ],
                "questions": [
                    "What's the digital transformation roadmap?",
                    "How does the PMO report?",
                    "What's the budget authority?"
                ]
            }
        else:
            return {
                "industry": "Technology/Professional Services",
                "size": "Medium-Large",
                "hq": "Regional",
                "talking_points": [
                    "Track record in similar transformations",
                    "Multi-country governance experience",
                    "Executive stakeholder management"
                ],
                "challenges": [
                    "Rapid growth scaling",
                    "Process standardization",
                    "Change management"
                ],
                "questions": [
                    "What's driving this hire?",
                    "Who will I report to?",
                    "What's the team size?"
                ]
            }
    
    # === 7. INTERVIEW NOTES DATABASE ===
    def interview_notes(self, company):
        """Create interview notes entry"""
        print("\n" + "="*60)
        print(f"📝 INTERVIEW NOTES: {company}")
        print("="*60)
        
        notes_template = {
            "company": company,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "interviewer": "",
            "role": "",
            "questions_asked": [],
            "topics_discussed": [],
            "questions_I_asked": [],
            "overall_impression": "",
            "follow_up_needed": [],
            "next_steps": "",
            "salary_discussed": False,
            "salary_mentioned": None
        }
        
        print(f"\n📋 TEMPLATE CREATED:")
        print(json.dumps(notes_template, indent=2))
        
        # Save to file
        notes_file = self.data_dir / f"interview_{company.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(notes_file, 'w') as f:
            json.dump(notes_template, f, indent=2)
        
        print(f"\n✅ Saved to: {notes_file}")
        
        return notes_template
    
    # === 8. SKILL GAP ANALYZER ===
    def skill_gap(self, role):
        """Analyze skill gaps"""
        print("\n" + "="*60)
        print(f"🔧 SKILL GAP ANALYSIS: {role}")
        print("="*60)
        
        # Required skills
        required = self.get_required_skills(role)
        
        # Current skills
        current = set(self.profile.get("skills", []))
        
        # Gap analysis
        required_set = set(required)
        matched = current.intersection(required_set)
        gaps = required_set - current
        plus = current - required_set
        
        print(f"\n✅ MATCHED SKILLS ({len(matched)}):")
        for s in matched:
            print(f"   • {s}")
        
        print(f"\n⚠️ SKILL GAPS ({len(gaps)}):")
        for s in gaps:
            print(f"   • {s}")
        
        print(f"\n💡 BONUS SKILLS ({len(plus)}):")
        for s in list(plus)[:5]:
            print(f"   • {s}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   • Focus on: {', '.join(list(gaps)[:3])}")
        print(f"   • Leverage: {', '.join(list(matched)[:3])}")
        
        return {
            "matched": list(matched),
            "gaps": list(gaps),
            "bonus": list(plus)
        }
    
    def get_required_skills(self, role):
        """Get required skills for role"""
        role_lower = role.lower()
        
        if "pmo" in role_lower or "program" in role_lower:
            return [
                "PMO Leadership", "Program Management", "Stakeholder Management",
                "Budget Management", "Risk Management", "Agile", "SAFe",
                "Governance", "Executive Reporting", "Transformation"
            ]
        elif "data" in role_lower or "ai" in role_lower:
            return [
                "Data Governance", "Data Quality", "Metadata Management",
                "AI/ML Programs", "Analytics", "Stakeholder Management",
                "Regulatory Compliance", "Transformation"
            ]
        else:
            return [
                "Leadership", "Strategy", "Stakeholder Management",
                "Program Management", "Transformation"
            ]
    
    # === 9. MULTI-LANGUAGE CV ===
    def cv_multi(self, role, lang):
        """Generate CV in different language format"""
        print("\n" + "="*60)
        print(f"🌍 MULTI-LANGUAGE CV: {lang.upper()}")
        print("="*60)
        
        translations = {
            "ar": {
                "title": "Director of Programs",
                "summary": "مشغل برنامج رائد مع أكثر من 20 عامًا من الخبرة في قيادة مبادرات التحول الرقمي في منطقة الخليج.",
                "experience": "الخبرة",
                "education": "التعليم"
            },
            "fr": {
                "title": "Directeur de Programmes",
                "summary": "Leader de programme accompli avec plus de 20 ans d'expérience dans la conduite de transformations numériques au Moyen-Orient.",
                "experience": "Expérience",
                "education": "Éducation"
            }
        }
        
        if lang in translations:
            t = translations[lang]
            print(f"\n📄 {t['title'].upper()}")
            print(f"\n{t['summary']}")
            print(f"\n{t['experience']}: Program Leadership, PMO, Transformation")
            print(f"{t['education']}: MBA (in progress), PMP")
        else:
            print(f"\n⚠️ Language '{lang}' not yet supported")
            print("Supported: ar (Arabic), fr (French)")
        
        return translations.get(lang, {})
    
    # === 10. MARKET TRENDS TRACKER ===
    def market_trends(self, sector):
        """Track market trends"""
        print("\n" + "="*60)
        print(f"📈 MARKET TRENDS: {sector}")
        print("="*60)
        
        trends = self.get_market_trends(sector)
        
        print(f"\n🔥 TOP TRENDS:")
        for t in trends["hot_trends"]:
            print(f"   • {t}")
        
        print(f"\n📉 DECLINING:")
        for t in trends["declining"]:
            print(f"   • {t}")
        
        print(f"\n💡 OPPORTUNITIES:")
        for t in trends["opportunities"]:
            print(f"   • {t}")
        
        print(f"\n⚠️ THREATS:")
        for t in trends["threats"]:
            print(f"   • {t}")
        
        return trends
    
    def get_market_trends(self, sector):
        """Get market trends for sector"""
        if sector.lower() == "pmo" or "program" in sector.lower():
            return {
                "hot_trends": [
                    "AI-integrated PMO tools",
                    "Hybrid Agile-Waterfall",
                    "OKR-Integrated Governance",
                    "Remote Program Management"
                ],
                "declining": [
                    "Traditional PMO bureaucracies",
                    "Manual reporting"
                ],
                "opportunities": [
                    "Data-driven PMO",
                    "Strategic PMO as profit center"
                ],
                "threats": [
                    "AI replacing traditional PM roles",
                    "Remote work governance challenges"
                ]
            }
        else:
            return {
                "hot_trends": [
                    "Digital transformation acceleration",
                    "AI/ML integration",
                    "Cloud migration"
                ],
                "declining": [
                    "Legacy systems"
                ],
                "opportunities": [
                    "GCC market growth"
                ],
                "threats": [
                    "Economic uncertainty"
                ]
            }


if __name__ == "__main__":
    import sys
    
    suite = IntelligenceSuite()
    
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        command = sys.argv[1]
        
        if command == "jd-analyze":
            jd = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "PMO Director with 10+ years experience in financial services"
            suite.jd_analyze(jd)
        elif command == "interview-prep":
            role = sys.argv[2] if len(sys.argv) > 2 else "PMO Director"
            company = sys.argv[3] if len(sys.argv) > 3 else "Company"
            suite.interview_prep(role, company)
        elif command == "salary-benchmark":
            role = sys.argv[2] if len(sys.argv) > 2 else "PMO Director"
            suite.salary_benchmark(role)
        elif command == "linkedin-post":
            topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "program leadership"
            suite.linkedin_post(topic)
        elif command == "email-followup":
            company = sys.argv[2] if len(sys.argv) > 2 else "Company"
            suite.email_followup(company)
        elif command == "company-research":
            company = sys.argv[2] if len(sys.argv) > 2 else "Company"
            suite.company_research(company)
        elif command == "interview-notes":
            company = sys.argv[2] if len(sys.argv) > 2 else "Company"
            suite.interview_notes(company)
        elif command == "skill-gap":
            role = sys.argv[2] if len(sys.argv) > 2 else "PMO Director"
            suite.skill_gap(role)
        elif command == "cv-multi":
            role = sys.argv[2] if len(sys.argv) > 2 else "Director"
            lang = sys.argv[3] if len(sys.argv) > 3 else "ar"
            suite.cv_multi(role, lang)
        elif command == "market-trends":
            sector = sys.argv[2] if len(sys.argv) > 2 else "PMO"
            suite.market_trends(sector)
        else:
            print(__doc__)
