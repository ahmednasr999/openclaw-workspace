#!/usr/bin/env python3
"""
Generate COMPLETE Head of AI Advisory CV for eMagine Solutions
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
import os

output_path = "/root/.openclaw/workspace/cvs/Ahmed Nasr - Head of AI Advisory - eMagine Solutions.pdf"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

doc = SimpleDocTemplate(output_path, pagesize=A4,
    topMargin=0.4*inch, bottomMargin=0.4*inch,
    leftMargin=0.6*inch, rightMargin=0.6*inch)

styles = getSampleStyleSheet()
story = []

# Styles
name_s = ParagraphStyle('Name', fontSize=20, alignment=1, spaceAfter=2, fontName='Helvetica-Bold')
contact_s = ParagraphStyle('Contact', fontSize=9, alignment=1, spaceAfter=6, textColor=colors.HexColor('#333333'))
section_s = ParagraphStyle('Section', fontSize=11, spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1a1a1a'), borderWidth=0, borderPadding=0)
role_s = ParagraphStyle('Role', fontSize=10, spaceBefore=6, spaceAfter=2, fontName='Helvetica-Bold')
bullet_s = ParagraphStyle('Bullet', fontSize=9, leftIndent=12, spaceAfter=2, fontName='Helvetica',
    bulletIndent=0, bulletFontName='Helvetica', bulletFontSize=9)
normal_s = ParagraphStyle('Norm', fontSize=9, spaceAfter=2, fontName='Helvetica')
small_s = ParagraphStyle('Small', fontSize=8.5, spaceAfter=1, fontName='Helvetica', textColor=colors.HexColor('#444444'))

def add_section(title):
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    story.append(Paragraph(title, section_s))

def add_role(title, company, location, dates):
    story.append(Paragraph(f"<b>{title}</b>", role_s))
    story.append(Paragraph(f"{company} | {location} | {dates}", small_s))

def add_bullet(text):
    story.append(Paragraph(f"\u2022 {text}", bullet_s))

# Header
story.append(Paragraph("AHMED NASR", name_s))
story.append(Paragraph("Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr", contact_s))

# Executive Summary
add_section("EXECUTIVE SUMMARY")
story.append(Paragraph(
    "Digital Transformation & AI Executive with 20+ years driving measurable business impact across "
    "FinTech, HealthTech, and e-commerce in GCC and Egypt. Expertise in enterprise AI deployment, "
    "AI advisory, and leading digital transformation at scale. Currently leading $50M digital "
    "transformation across a 15-hospital network, deploying 14 production AI agents in live clinical "
    "operations. Built enterprise PMO managing 300+ concurrent projects across 8 countries. "
    "Scaled Talabat from 30K to 7M daily orders (233x growth). Combines strategic vision with "
    "operational excellence to deliver transformation programs that drive efficiency, improve outcomes, "
    "and create sustainable growth.", normal_s))

# Core Competencies
add_section("CORE COMPETENCIES")
story.append(Paragraph(
    "Enterprise AI & AI Advisory | Digital Transformation Strategy | Generative AI & LLM Deployment | "
    "AI Governance & Ethics | PMO & Portfolio Leadership | Healthcare AI & Clinical Decision Support | "
    "Cloud Platform Strategy (AWS, Azure) | Change Management & Organizational Transformation | "
    "Stakeholder & Vendor Management | Program & Project Management | FinTech Architecture | "
    "Data Analytics & Business Intelligence", normal_s))

# Professional Experience
add_section("PROFESSIONAL EXPERIENCE")

# Role 1: SGH
add_role("PMO & Regional Engagement Lead", "Saudi German Hospital Group (TopMed)", "Dubai, UAE", "Jun 2024 - Present")
add_bullet("Leading $50M digital transformation across 15-hospital network in KSA, UAE, and Egypt, managing cross-functional teams of 30 professionals")
add_bullet("Deploying 14 production AI agents in live clinical operations, integrating GenAI for clinical decision support, automated reporting, and patient flow optimization")
add_bullet("Established enterprise PMO framework with standardized governance model for technology project delivery across the hospital network")
add_bullet("Partnering with U.S. healthcare technology leaders to implement Health Catalyst enterprise data platform, enabling AI-assisted clinical and financial benchmarking")
add_bullet("Deploying KLAS-rated healthcare IT solutions at enterprise scale, unifying clinical, financial, and operational data across 15 facilities")

# Role 2: PaySky
add_role("Country Manager", "PaySky, Inc.", "Egypt", "Apr 2021 - Jan 2022")
add_bullet("Led market entry strategy and product architecture for Egypt's first comprehensive SuperApp integrating payments, banking, e-commerce, and AI-driven personalization")
add_bullet("Designed SuperApp architecture with AI-powered recommendation engine for financial services and digital inclusion for underbanked populations")
add_bullet("Established strategic partnerships with financial institutions and service providers to build comprehensive platform ecosystem")
add_bullet("Built initial team and operational framework for phased market launch and product rollout")

# Role 3: Al Araby
add_role("Head of E-Commerce Product & IT Strategy", "Al Araby Group", "Egypt", "Jan 2020 - Jan 2021")
add_bullet("Led e-commerce digital transformation and IT strategy for one of Egypt's largest consumer electronics and home appliances retailers")
add_bullet("Implemented AI-powered inventory management, customer analytics, and personalization systems")

# Role 4: Talabat
add_role("Product Development Manager", "Delivery Hero SE (Talabat)", "GCC Markets", "Jun 2017 - May 2018")
add_bullet("Led product strategy and operational improvements during hypergrowth, scaling platform from 30,000 to 7 million daily orders across GCC markets (233x growth)")
add_bullet("Drove product strategic direction and feature prioritization supporting rapid scaling across Egypt and GCC countries")
add_bullet("Led Operations Excellence Committee coordinating initiatives between Berlin HQ, GCC countries, and Egypt markets")
add_bullet("Implemented lean methodologies and managed cross-functional product and design teams delivering customer-centric features")

# Role 5: Network International
add_role("PMO Section Head (Project Management Department Manager)", "Network International", "Egypt", "Sep 2014 - Jun 2017")
add_bullet("Built and led enterprise PMO from ground up managing 300+ concurrent banking and payments projects across 8 countries (Egypt, UAE, Jordan, Kenya, Nigeria, Ghana, Mauritius, South Africa)")
add_bullet("Recruited and trained team of 16 Project Managers managing portfolio serving 300+ banking clients worldwide")
add_bullet("Implemented directive PMO framework and governance model, standardizing project delivery methodology across emerging markets payments division")
add_bullet("Delivered comprehensive mobile commerce and digital payments portfolio including mobile wallets, cardless transactions, and cross-border money transfer solutions")
add_bullet("Governed 14-month Salesforce enterprise implementation across 8 countries (170 users)")

# Role 6: Revamp
add_role("Engagement Manager", "Revamp Consulting", "USA, UAE, Egypt", "Mar 2013 - Sep 2014")
add_bullet("Managed multi-sector consulting engagements for enterprise clients including Mayo Clinic (healthcare business process optimization) and AT&T (service operations transformation)")

# Earlier Experience
story.append(Paragraph("<b>Earlier Experience (2004-2013)</b>", role_s))
add_bullet("Senior Project Manager, PMO | BlueCloud (2012-2013): IT infrastructure projects for Microsoft Egypt, Vodafone Egypt, Qatar Diar")
add_bullet("Project Manager | Intel Corporation (2011-2012): LTE (4G) mobile technology deployment")
add_bullet("Technical Leadership Roles | BASS, Code Republic, Speech Workers, PEARDEV (2004-2009): Software development and project delivery")

# Education
add_section("EDUCATION")
story.append(Paragraph("<b>MBA, Master in International Business Administration</b> | Paris ESLSCA Business School | 2025-2027 (In Progress)", normal_s))
story.append(Paragraph("<b>BSc Computer Science</b> | Ain Shams University, Egypt", normal_s))

# Certifications
add_section("CERTIFICATIONS")
story.append(Paragraph(
    "PMP (Project Management Professional) | CSM (Certified Scrum Master) | "
    "CSPO (Certified Scrum Product Owner) | Lean Six Sigma (Black Belt) | "
    "CBAP (Certified Business Analysis Professional) | ITIL Foundations", normal_s))

# Technical Skills
add_section("TECHNICAL SKILLS")
story.append(Paragraph(
    "AI & Machine Learning | Generative AI / LLM | Cloud Architecture (AWS, Azure, GCP) | "
    "Healthcare IT (Health Catalyst, KLAS) | FinTech & Payments | E-commerce Platforms | "
    "ERP Systems (SAP, Salesforce) | Data Analytics & BI | Agile, Scrum, Waterfall | "
    "Enterprise Architecture | Mobile Technologies", normal_s))

doc.build(story)
print(f"CV generated: {output_path}")
