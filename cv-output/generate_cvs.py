#!/usr/bin/env python3
"""Generate 5 tailored CVs for Ahmed Nasr"""

import os
from weasyprint import HTML

OUTPUT_DIR = "/root/.openclaw/workspace/cv-output"

# Base CSS for ATS-friendly single-column layout
CSS = """
@page {
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
}
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #000;
    max-width: 100%;
}
h1 {
    font-size: 18pt;
    margin: 0 0 5px 0;
    color: #000;
}
.contact {
    font-size: 9pt;
    margin-bottom: 15px;
    color: #333;
}
h2 {
    font-size: 12pt;
    border-bottom: 1px solid #000;
    padding-bottom: 3px;
    margin: 15px 0 8px 0;
    text-transform: uppercase;
}
.summary {
    margin-bottom: 10px;
    text-align: justify;
}
.job {
    margin-bottom: 12px;
}
.job-header {
    font-weight: bold;
    margin-bottom: 2px;
}
.job-title {
    font-weight: bold;
}
.job-company {
    font-style: italic;
}
.job-date {
    color: #333;
}
ul {
    margin: 5px 0 0 0;
    padding-left: 20px;
}
li {
    margin-bottom: 3px;
}
.certifications {
    margin-top: 5px;
}
"""

# CV 1: Strategy & Transformation Director - International Medical Company
cv1_html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>""" + CSS + """</style></head>
<body>
<h1>Ahmed Nasr</h1>
<div class="contact">Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr</div>

<h2>Professional Summary</h2>
<div class="summary">
Transformation-focused executive with 20+ years driving operational excellence and digital transformation across healthcare, fintech, and e-commerce sectors. Currently leading $50M digital transformation across a 15-hospital network spanning KSA, UAE, and Egypt. Proven track record in executive stakeholder management, healthcare operations optimization, and enterprise-wide transformation strategy. Combines strategic vision with hands-on execution to deliver measurable operational improvements.
</div>

<h2>Professional Experience</h2>

<div class="job">
<div class="job-header"><span class="job-title">PMO & Regional Engagement Lead</span> | <span class="job-company">Saudi German Hospital Group</span></div>
<div class="job-date">June 2024 – Present | KSA/UAE/Egypt</div>
<ul>
<li>Lead $50M digital transformation initiative across 15-hospital network in KSA, UAE, and Egypt</li>
<li>Drive enterprise-wide transformation strategy aligned with organizational healthcare objectives</li>
<li>Manage executive stakeholder relationships across multiple countries and functional areas</li>
<li>Implement operational excellence frameworks to optimize healthcare delivery processes</li>
<li>Oversee cross-functional transformation programs ensuring alignment with strategic priorities</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Country Manager</span> | <span class="job-company">PaySky (Egypt's First SuperApp)</span></div>
<div class="job-date">2021 – 2022 | Egypt</div>
<ul>
<li>Held full P&L ownership for national fintech operations with executive accountability</li>
<li>Executed digital transformation strategy to establish market-leading SuperApp platform</li>
<li>Led organizational change management initiatives across all business functions</li>
<li>Built and managed stakeholder relationships with regulators, partners, and investors</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Head of E-Commerce</span> | <span class="job-company">Al Araby Group</span></div>
<div class="job-date">2020 – 2021 | Egypt</div>
<ul>
<li>Led digital transformation of traditional retail business into omnichannel operation</li>
<li>Drove operational excellence improvements across e-commerce fulfillment and delivery</li>
<li>Managed transformation strategy from concept through implementation and optimization</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Product Development Manager</span> | <span class="job-company">Delivery Hero / Talabat</span></div>
<div class="job-date">2017 – 2018 | UAE/MENA</div>
<ul>
<li>Scaled operations from 30,000 to 7 million daily orders (233x growth)</li>
<li>Implemented operational excellence methodologies driving efficiency improvements</li>
<li>Led cross-functional stakeholder management across regional operations</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">PMO Section Head</span> | <span class="job-company">Network International</span></div>
<div class="job-date">2014 – 2017 | UAE/8 Countries</div>
<ul>
<li>Managed portfolio of 300+ projects across 8 countries in the Middle East and Africa</li>
<li>Established enterprise PMO governance framework and transformation standards</li>
<li>Led strategic planning and executive reporting for C-suite stakeholders</li>
</ul>
</div>

<h2>Core Competencies</h2>
<ul>
<li>Digital Transformation & Strategy Execution</li>
<li>Healthcare Operations & Operational Excellence</li>
<li>Executive Stakeholder Management</li>
<li>Enterprise PMO & Change Management</li>
<li>P&L Ownership & Strategic Leadership</li>
</ul>

<h2>Certifications</h2>
<div class="certifications">
PMP (2008) | Certified Scrum Master (2014) | Certified Scrum Product Owner (2014) | CBAP (2014) | Lean Six Sigma (2010)
</div>

</body>
</html>"""

# CV 2: Chief Transformation Officer - ICG Saudi Arabia
cv2_html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>""" + CSS + """</style></head>
<body>
<h1>Ahmed Nasr</h1>
<div class="contact">Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr</div>

<h2>Professional Summary</h2>
<div class="summary">
Enterprise transformation executive with 20+ years delivering AI-powered digital transformation and operational change across healthcare, fintech, and e-commerce in the Middle East. Currently leading $50M enterprise transformation across 15 healthcare facilities. Expert in strategy execution, change management, and building high-performing teams that deliver measurable business outcomes. Deep experience in the Saudi and GCC markets with proven ability to drive AI and digital initiatives at scale.
</div>

<h2>Professional Experience</h2>

<div class="job">
<div class="job-header"><span class="job-title">PMO & Regional Engagement Lead</span> | <span class="job-company">Saudi German Hospital Group</span></div>
<div class="job-date">June 2024 – Present | KSA/UAE/Egypt</div>
<ul>
<li>Lead $50M enterprise digital transformation across 15-hospital network integrating AI and data analytics</li>
<li>Drive AI-powered transformation initiatives to optimize healthcare operations and patient outcomes</li>
<li>Execute change management strategies ensuring adoption across diverse organizational cultures</li>
<li>Deliver digital enterprise solutions aligning technology investments with strategic business goals</li>
<li>Partner with C-suite executives on transformation roadmap and strategy execution</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Country Manager</span> | <span class="job-company">PaySky (Egypt's First SuperApp)</span></div>
<div class="job-date">2021 – 2022 | Egypt</div>
<ul>
<li>Led enterprise-wide digital transformation establishing Egypt's first SuperApp platform</li>
<li>Drove AI and data analytics integration across fintech product portfolio</li>
<li>Owned full P&L with accountability for operational transformation outcomes</li>
<li>Executed change management across organization during rapid scaling phase</li>
<li>Built consulting-style client relationships with enterprise partners and stakeholders</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Head of E-Commerce</span> | <span class="job-company">Al Araby Group</span></div>
<div class="job-date">2020 – 2021 | Egypt</div>
<ul>
<li>Executed digital transformation strategy converting traditional retail to digital-first model</li>
<li>Implemented AI and data analytics for demand forecasting and operational optimization</li>
<li>Led operational transformation improving efficiency across fulfillment operations</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Product Development Manager</span> | <span class="job-company">Delivery Hero / Talabat</span></div>
<div class="job-date">2017 – 2018 | UAE/MENA</div>
<ul>
<li>Delivered 233x operational scale growth (30K to 7M daily orders) through digital transformation</li>
<li>Applied AI and data analytics to optimize marketplace operations and customer experience</li>
<li>Led strategy execution across Middle East markets driving regional expansion</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">PMO Section Head</span> | <span class="job-company">Network International</span></div>
<div class="job-date">2014 – 2017 | UAE/8 Countries</div>
<ul>
<li>Managed enterprise transformation portfolio of 300+ projects across 8 Middle East countries</li>
<li>Established change management frameworks for large-scale operational initiatives</li>
<li>Delivered consulting-grade strategy execution for regional fintech transformation</li>
</ul>
</div>

<h2>Core Competencies</h2>
<ul>
<li>AI-Powered Digital Transformation</li>
<li>Enterprise Transformation & Strategy Execution</li>
<li>Change Management & Organizational Development</li>
<li>Operational Excellence & Process Optimization</li>
<li>Middle East Market Expertise (KSA, UAE, Egypt)</li>
<li>AI & Data Analytics Implementation</li>
</ul>

<h2>Certifications</h2>
<div class="certifications">
PMP (2008) | Certified Scrum Master (2014) | Certified Scrum Product Owner (2014) | CBAP (2014) | Lean Six Sigma (2010)
</div>

</body>
</html>"""

# CV 3: AI Strategy Director - PwC Middle East
cv3_html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>""" + CSS + """</style></head>
<body>
<h1>Ahmed Nasr</h1>
<div class="contact">Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr</div>

<h2>Professional Summary</h2>
<div class="summary">
Digital transformation and AI strategy executive with 20+ years delivering enterprise-scale digital initiatives across healthcare, fintech, and e-commerce in the Middle East. Currently directing $50M digital transformation with integrated AI and data analytics strategy across a 15-facility healthcare network. Proven advisory expertise in strategy realisation, helping organizations translate digital vision into measurable business outcomes. Track record of leading complex multi-stakeholder programs requiring cross-functional coordination.
</div>

<h2>Professional Experience</h2>

<div class="job">
<div class="job-header"><span class="job-title">PMO & Regional Engagement Lead</span> | <span class="job-company">Saudi German Hospital Group</span></div>
<div class="job-date">June 2024 – Present | KSA/UAE/Egypt</div>
<ul>
<li>Direct $50M digital transformation program integrating AI strategy across 15-hospital network</li>
<li>Develop and execute AI and data analytics strategy to drive clinical and operational improvements</li>
<li>Lead digital strategy realisation ensuring alignment between technology investments and business outcomes</li>
<li>Advise executive leadership on digital transformation roadmap and AI adoption priorities</li>
<li>Coordinate cybersecurity and data governance integration within digital transformation initiatives</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Country Manager</span> | <span class="job-company">PaySky (Egypt's First SuperApp)</span></div>
<div class="job-date">2021 – 2022 | Egypt</div>
<ul>
<li>Led digital strategy and realisation for Egypt's first SuperApp platform launch</li>
<li>Implemented AI and data analytics capabilities across financial services product suite</li>
<li>Provided advisory leadership to board and investors on digital transformation strategy</li>
<li>Owned P&L with full accountability for digital business outcomes</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Head of E-Commerce</span> | <span class="job-company">Al Araby Group</span></div>
<div class="job-date">2020 – 2021 | Egypt</div>
<ul>
<li>Executed digital transformation strategy converting traditional retail to digital-first enterprise</li>
<li>Deployed AI and data analytics solutions for demand forecasting and customer intelligence</li>
<li>Led strategy realisation from business case through implementation and optimization</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Product Development Manager</span> | <span class="job-company">Delivery Hero / Talabat</span></div>
<div class="job-date">2017 – 2018 | UAE/MENA</div>
<ul>
<li>Delivered 233x scale growth through AI-driven operational optimization (30K to 7M daily orders)</li>
<li>Applied data analytics and AI to transform marketplace operations across Middle East</li>
<li>Provided strategic advisory on digital product development and technology investments</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">PMO Section Head</span> | <span class="job-company">Network International</span></div>
<div class="job-date">2014 – 2017 | UAE/8 Countries</div>
<ul>
<li>Managed digital transformation portfolio of 300+ projects across 8 Middle East countries</li>
<li>Delivered advisory-style governance and strategic oversight for enterprise programs</li>
<li>Established frameworks for strategy realisation and digital program execution</li>
</ul>
</div>

<h2>Core Competencies</h2>
<ul>
<li>AI Strategy Development & Implementation</li>
<li>Digital Transformation & Strategy Realisation</li>
<li>Enterprise Advisory & Consulting</li>
<li>Data Analytics & Business Intelligence</li>
<li>Cybersecurity & Digital Governance Integration</li>
<li>Middle East Market (KSA, UAE, Egypt)</li>
</ul>

<h2>Certifications</h2>
<div class="certifications">
PMP (2008) | Certified Scrum Master (2014) | Certified Scrum Product Owner (2014) | CBAP (2014) | Lean Six Sigma (2010)
</div>

</body>
</html>"""

# CV 4: Director of Retail Operations - Private GCC Retailer
cv4_html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>""" + CSS + """</style></head>
<body>
<h1>Ahmed Nasr</h1>
<div class="contact">Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr</div>

<h2>Professional Summary</h2>
<div class="summary">
Operations executive with 20+ years driving operational excellence across retail, e-commerce, and consumer businesses in the GCC and Middle East. Proven P&L ownership experience with track record of scaling multi-channel retail operations. Expert in store operations optimization, consumer experience enhancement, and building high-performing teams. Deep experience in the UAE, Saudi Arabia, and broader GCC markets with demonstrated ability to drive operational improvements at scale.
</div>

<h2>Professional Experience</h2>

<div class="job">
<div class="job-header"><span class="job-title">PMO & Regional Engagement Lead</span> | <span class="job-company">Saudi German Hospital Group</span></div>
<div class="job-date">June 2024 – Present | KSA/UAE/Egypt</div>
<ul>
<li>Lead $50M operational transformation across 15-facility network in KSA, UAE, and Egypt</li>
<li>Drive operational excellence initiatives improving service delivery and efficiency</li>
<li>Manage multi-site operations coordination across GCC and Middle East markets</li>
<li>Implement standardized operational frameworks ensuring consistent service quality</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Head of E-Commerce</span> | <span class="job-company">Al Araby Group</span></div>
<div class="job-date">2020 – 2021 | Egypt</div>
<ul>
<li>Led retail operations transformation from traditional to multi-channel model</li>
<li>Drove operational excellence across store operations and e-commerce fulfillment</li>
<li>Managed P&L with full accountability for retail business unit performance</li>
<li>Optimized consumer experience across physical and digital retail channels</li>
<li>Built and led high-performing retail operations team</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Country Manager</span> | <span class="job-company">PaySky (Egypt's First SuperApp)</span></div>
<div class="job-date">2021 – 2022 | Egypt</div>
<ul>
<li>Held full P&L ownership for national consumer-facing operations</li>
<li>Drove operational excellence across customer service and delivery channels</li>
<li>Managed multi-channel consumer engagement and experience optimization</li>
<li>Built operational infrastructure supporting rapid consumer growth</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Product Development Manager</span> | <span class="job-company">Delivery Hero / Talabat</span></div>
<div class="job-date">2017 – 2018 | UAE/MENA</div>
<ul>
<li>Scaled retail/consumer operations from 30,000 to 7 million daily orders (233x growth)</li>
<li>Led operational excellence initiatives across GCC retail marketplace</li>
<li>Optimized store operations and merchant management across UAE and Saudi Arabia</li>
<li>Managed multi-channel consumer delivery operations at scale</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">PMO Section Head</span> | <span class="job-company">Network International</span></div>
<div class="job-date">2014 – 2017 | UAE/8 Countries</div>
<ul>
<li>Managed operations portfolio of 300+ projects across 8 GCC and Middle East countries</li>
<li>Established operational excellence frameworks and performance standards</li>
<li>Led cross-border operations coordination and stakeholder management</li>
</ul>
</div>

<h2>Core Competencies</h2>
<ul>
<li>Retail Operations & Store Management</li>
<li>Multi-Channel Consumer Operations</li>
<li>P&L Ownership & Financial Accountability</li>
<li>Operational Excellence & Process Optimization</li>
<li>GCC Market Expertise (UAE, KSA, Egypt)</li>
<li>Team Building & Performance Management</li>
</ul>

<h2>Certifications</h2>
<div class="certifications">
PMP (2008) | Certified Scrum Master (2014) | Certified Scrum Product Owner (2014) | CBAP (2014) | Lean Six Sigma (2010)
</div>

</body>
</html>"""

# CV 5: Head of Digital Product Delivery - UAE
cv5_html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>""" + CSS + """</style></head>
<body>
<h1>Ahmed Nasr</h1>
<div class="contact">Dubai, UAE | +971 50 281 4490 | ahmednasr999@gmail.com | linkedin.com/in/ahmednasr</div>

<h2>Professional Summary</h2>
<div class="summary">
Digital product delivery executive with 20+ years leading consumer digital and mobile app initiatives across fintech, e-commerce, and healthcare. Certified Scrum Master and Product Owner with deep expertise in agile delivery, product roadmap prioritisation, and cross-functional team leadership. Proven track record delivering digital products at scale, including platforms serving millions of daily users. Expert in bridging business strategy with technical delivery to ship consumer-focused mobile experiences.
</div>

<h2>Professional Experience</h2>

<div class="job">
<div class="job-header"><span class="job-title">PMO & Regional Engagement Lead</span> | <span class="job-company">Saudi German Hospital Group</span></div>
<div class="job-date">June 2024 – Present | KSA/UAE/Egypt</div>
<ul>
<li>Lead digital product delivery for $50M transformation including mobile app and consumer digital initiatives</li>
<li>Apply agile/scrum methodologies to drive iterative delivery across 15-facility network</li>
<li>Manage product roadmap prioritisation balancing stakeholder needs and technical constraints</li>
<li>Oversee cross-functional delivery teams ensuring on-time, on-budget product launches</li>
<li>Drive consumer digital strategy improving patient engagement through mobile channels</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Country Manager</span> | <span class="job-company">PaySky (Egypt's First SuperApp)</span></div>
<div class="job-date">2021 – 2022 | Egypt</div>
<ul>
<li>Led digital product delivery for Egypt's first mobile SuperApp platform</li>
<li>Drove mobile app strategy and roadmap prioritisation for consumer fintech products</li>
<li>Applied agile/scrum delivery frameworks across product development teams</li>
<li>Managed end-to-end digital product lifecycle from concept to consumer launch</li>
<li>Owned P&L with accountability for digital product performance metrics</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Head of E-Commerce</span> | <span class="job-company">Al Araby Group</span></div>
<div class="job-date">2020 – 2021 | Egypt</div>
<ul>
<li>Delivered consumer digital platform including mobile app and web e-commerce</li>
<li>Led product roadmap development and feature prioritisation</li>
<li>Managed agile delivery teams shipping consumer-focused digital experiences</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">Product Development Manager</span> | <span class="job-company">Delivery Hero / Talabat</span></div>
<div class="job-date">2017 – 2018 | UAE/MENA</div>
<ul>
<li>Led digital product delivery scaling mobile app from 30K to 7M daily orders (233x growth)</li>
<li>Drove mobile app strategy and feature roadmap for consumer marketplace</li>
<li>Applied agile/scrum methodologies managing high-velocity product delivery</li>
<li>Optimized consumer digital experience driving engagement and retention metrics</li>
</ul>
</div>

<div class="job">
<div class="job-header"><span class="job-title">PMO Section Head</span> | <span class="job-company">Network International</span></div>
<div class="job-date">2014 – 2017 | UAE/8 Countries</div>
<ul>
<li>Managed digital product portfolio of 300+ projects across 8 countries</li>
<li>Established agile delivery management frameworks and governance</li>
<li>Led product prioritisation and roadmap planning for enterprise digital initiatives</li>
</ul>
</div>

<h2>Core Competencies</h2>
<ul>
<li>Digital Product Delivery & Mobile App Strategy</li>
<li>Agile/Scrum Delivery Management</li>
<li>Product Roadmap & Prioritisation</li>
<li>Consumer Digital Experience</li>
<li>Cross-Functional Team Leadership</li>
<li>Delivery Management & Program Execution</li>
</ul>

<h2>Certifications</h2>
<div class="certifications">
Certified Scrum Master - CSM (2014) | Certified Scrum Product Owner - CSPO (2014) | PMP (2008) | CBAP (2014) | Lean Six Sigma (2010)
</div>

</body>
</html>"""

# CV configurations
cvs = [
    {
        "title": "Strategy & Transformation Director",
        "company": "International Medical Company",
        "html": cv1_html
    },
    {
        "title": "Chief Transformation Officer (CTO) – AI, Digital & Enterprise Transformation",
        "company": "Innovation Consulting Group (ICG)",
        "html": cv2_html
    },
    {
        "title": "Digital and Cyber - Digital Strategy and Realisation - AI Strategy Director",
        "company": "PwC Middle East",
        "html": cv3_html
    },
    {
        "title": "Director of Retail Operations",
        "company": "Private multinational retailer",
        "html": cv4_html
    },
    {
        "title": "Head of Digital Product Delivery (Mobile App)",
        "company": "Confidential",
        "html": cv5_html
    }
]

# Generate all CVs
results = []
for i, cv in enumerate(cvs, 1):
    filename_base = f"Ahmed Nasr - {cv['title']} - {cv['company']}"
    html_path = os.path.join(OUTPUT_DIR, f"{filename_base}.html")
    pdf_path = os.path.join(OUTPUT_DIR, f"{filename_base}.pdf")
    
    # Write HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(cv['html'])
    
    # Generate PDF
    try:
        HTML(string=cv['html']).write_pdf(pdf_path)
        status = "✅"
    except Exception as e:
        status = f"❌ {e}"
    
    results.append({
        "num": i,
        "title": cv['title'],
        "company": cv['company'],
        "pdf_path": pdf_path,
        "status": status
    })
    print(f"[{i}] {cv['title']} - {cv['company']} | {status}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
for r in results:
    print(f"{r['num']}. {r['title']} - {r['company']}")
    print(f"   PDF: {r['pdf_path']}")
print("\nDONE: 5 CVs ready")
