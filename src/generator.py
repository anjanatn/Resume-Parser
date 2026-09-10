import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def build_pdf_resume(filename, candidate_data, layout_style='classic'):
    """
    Builds a professional PDF resume using ReportLab.
    Supports styles: 'classic', 'modern_header'.
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#1E3A8A') if layout_style != 'modern_header' else colors.HexColor('#0F172A')
    secondary_color = colors.HexColor('#3B82F6')
    text_color = colors.HexColor('#1F2937')
    
    name_style = ParagraphStyle(
        'HeaderName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=TA_CENTER if layout_style == 'classic' else TA_LEFT
    )
    
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=15,
        textColor=secondary_color,
        alignment=TA_CENTER if layout_style == 'classic' else TA_LEFT
    )
    
    contact_style = ParagraphStyle(
        'HeaderContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4B5563'),
        alignment=TA_CENTER if layout_style == 'classic' else TA_LEFT
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=text_color
    )

    story = []

    # 1. HEADER SECTION
    name = candidate_data['name']
    title = candidate_data['title']
    contacts = candidate_data['contacts']
    contact_str = "  •  ".join(contacts)

    if layout_style == 'modern_header':
        header_data = [
            [Paragraph(f"<b>{name}</b>", name_style)],
            [Paragraph(title, title_style)],
            [Paragraph(contact_str, contact_style)]
        ]
        t = Table(header_data, colWidths=[540])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))
    else:
        story.append(Paragraph(name, name_style))
        story.append(Spacer(1, 2))
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(contact_str, contact_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1, color=secondary_color, spaceAfter=8, spaceBefore=4))

    # 2. PROFESSIONAL SUMMARY
    if 'summary' in candidate_data:
        story.append(Paragraph(candidate_data.get('summary_heading', 'PROFESSIONAL SUMMARY').upper(), section_heading_style))
        story.append(Paragraph(candidate_data['summary'], body_style))
        story.append(Spacer(1, 8))

    # 3. TECHNICAL SKILLS
    if 'skills' in candidate_data:
        story.append(Paragraph(candidate_data.get('skills_heading', 'TECHNICAL SKILLS').upper(), section_heading_style))
        skills_text = ", ".join(candidate_data['skills'])
        story.append(Paragraph(f"<b>Core Competencies:</b> {skills_text}", body_style))
        story.append(Spacer(1, 8))

    # 4. WORK EXPERIENCE
    if 'experience' in candidate_data:
        story.append(Paragraph(candidate_data.get('exp_heading', 'WORK EXPERIENCE').upper(), section_heading_style))
        for exp in candidate_data['experience']:
            role_comp = f"<b>{exp['role']}</b> | {exp['company']}"
            dates_loc = f"<b>{exp['dates']}</b> ({exp.get('location', '')})"
            
            exp_table_data = [[
                Paragraph(role_comp, body_style),
                Paragraph(dates_loc, ParagraphStyle('RightText', parent=body_style, alignment=TA_RIGHT))
            ]]
            t_exp = Table(exp_table_data, colWidths=[360, 180])
            t_exp.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(t_exp)
            
            for bullet in exp.get('bullets', []):
                bullet_p = Paragraph(f"• {bullet}", ParagraphStyle('BulletText', parent=body_style, leftIndent=10))
                story.append(bullet_p)
            story.append(Spacer(1, 6))

    # 5. EDUCATION
    if 'education' in candidate_data:
        story.append(Paragraph(candidate_data.get('edu_heading', 'EDUCATION').upper(), section_heading_style))
        for edu in candidate_data['education']:
            edu_str = f"<b>{edu['degree']}</b> - {edu['institution']}"
            edu_dates = edu.get('year', '')
            
            edu_table_data = [[
                Paragraph(edu_str, body_style),
                Paragraph(f"<b>{edu_dates}</b>", ParagraphStyle('RightText', parent=body_style, alignment=TA_RIGHT))
            ]]
            t_edu = Table(edu_table_data, colWidths=[400, 140])
            t_edu.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(t_edu)

    doc.build(story)

def generate_all_sample_resumes(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    candidates = [
        {
            "id": "resume_01_alex_chen",
            "layout": "classic",
            "name": "Alex Chen",
            "title": "Senior Python Developer & AI Engineer",
            "contacts": ["alex.chen@email.com", "(555) 234-5678", "San Francisco, CA", "github.com/alexchen-dev"],
            "summary_heading": "Professional Overview",
            "summary": "Passionate Senior Software Engineer with 5.5 years of experience architecting scalable backend systems, microservices, and AI-powered data pipelines using Python, FastAPI, and PyTorch. Proven track record of improving API performance by 40% and deploying cloud solutions on AWS.",
            "skills_heading": "Technical Skills & Tools",
            "skills": ["Python", "FastAPI", "Django", "PyTorch", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "Git", "CI/CD", "REST APIs", "Microservices"],
            "exp_heading": "Professional Experience",
            "experience": [
                {
                    "role": "Senior Software Engineer",
                    "company": "TechScale Solutions",
                    "dates": "Mar 2022 - Present",
                    "location": "San Francisco, CA",
                    "bullets": [
                        "Architected high-throughput Python FastAPI microservices serving over 2M daily API requests.",
                        "Integrated PyTorch machine learning models into production inference pipelines, cutting latency by 35%.",
                        "Led migration of legacy monolith to Docker containers and Kubernetes on AWS EKS."
                    ]
                },
                {
                    "role": "Python Developer",
                    "company": "DataFlow Innovations",
                    "dates": "Jun 2019 - Feb 2022",
                    "location": "San Jose, CA",
                    "bullets": [
                        "Developed backend RESTful services using Python, Django, and PostgreSQL for real-time data analytics.",
                        "Optimized database SQL queries and implemented Redis caching, reducing page load times by 50%.",
                        "Collaborated with cross-functional Agile engineering teams to deliver bi-weekly product releases."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "B.S. in Computer Science",
                    "institution": "Stanford University",
                    "year": "2015 - 2019"
                }
            ]
        },
        {
            "id": "resume_02_maria_garcia",
            "layout": "modern_header",
            "name": "Maria Garcia",
            "title": "Full-Stack Software Engineer (Python & React)",
            "contacts": ["maria.garcia@techmail.io", "+1 (415) 987-6543", "Austin, TX", "linkedin.com/in/mariagarcia-code"],
            "summary_heading": "Summary",
            "summary": "Versatile Full-Stack Engineer with 3.5 years of experience delivering robust web applications using Python, Django, React, and PostgreSQL. Dedicated to writing clean, maintainable code and building intuitive user interfaces.",
            "skills_heading": "Skills",
            "skills": ["Python", "React", "JavaScript", "TypeScript", "Django", "Flask", "HTML5", "CSS3", "Tailwind CSS", "PostgreSQL", "GraphQL", "Docker"],
            "exp_heading": "Work Experience",
            "experience": [
                {
                    "role": "Full-Stack Software Engineer",
                    "company": "CloudScale Tech",
                    "dates": "Jan 2023 - Present",
                    "location": "Austin, TX",
                    "bullets": [
                        "Built responsive React dashboards backed by Python Django REST APIs for cloud resource monitoring.",
                        "Implemented JWT authentication and role-based authorization for enterprise SaaS clients.",
                        "Wrote unit and end-to-end test suites, maintaining 90%+ code coverage across backend and frontend."
                    ]
                },
                {
                    "role": "Software Developer",
                    "company": "WebCraft Studio",
                    "dates": "Aug 2021 - Dec 2022",
                    "location": "Dallas, TX",
                    "bullets": [
                        "Created custom web applications with Flask, React, and Tailwind CSS for client e-commerce platforms.",
                        "Integrated third-party payment gateways (Stripe, PayPal) and webhooks securely."
                    ]
                }
            ],
            "edu_heading": "Education & Degrees",
            "education": [
                {
                    "degree": "Bachelor of Science in Software Engineering",
                    "institution": "University of Texas at Austin",
                    "year": "2017 - 2021"
                }
            ]
        },
        {
            "id": "resume_03_david_smith",
            "layout": "classic",
            "name": "David Smith",
            "title": "Junior Data Analyst",
            "contacts": ["d.smith92@gmail.com", "(312) 555-0199", "Chicago, IL"],
            "summary_heading": "Career Summary",
            "summary": "Detail-oriented Junior Data Analyst with 1.5 years of experience extracting data insights, building interactive Tableau dashboards, and performing quantitative analysis using Python, SQL, and Pandas.",
            "skills_heading": "Core Skills",
            "skills": ["Python", "SQL", "Pandas", "NumPy", "Tableau", "PowerBI", "Microsoft Excel", "Matplotlib", "Statistics", "Data Cleaning"],
            "exp_heading": "Experience",
            "experience": [
                {
                    "role": "Junior Data Analyst",
                    "company": "Retail Insights Inc.",
                    "dates": "Mar 2023 - Present",
                    "location": "Chicago, IL",
                    "bullets": [
                        "Queried complex relational databases using SQL to extract customer retention and sales metrics.",
                        "Automated weekly reporting pipelines in Python using Pandas, saving 8 hours of manual work weekly.",
                        "Designed executive dashboards in Tableau visualizing key performance indicators for leadership."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "B.S. in Statistics",
                    "institution": "Northwestern University",
                    "year": "2019 - 2023"
                }
            ]
        },
        {
            "id": "resume_04_priya_sharma",
            "layout": "modern_header",
            "name": "Priya Sharma",
            "title": "DevOps & Cloud Infrastructure Lead",
            "contacts": ["priya.sharma@cloudnet.org", "(408) 555-7890", "Seattle, WA", "linkedin.com/in/priyasharma-devops"],
            "summary_heading": "Executive Summary",
            "summary": "Results-driven Cloud Architect & DevOps Lead with 7+ years of experience managing multi-region AWS cloud infrastructure, Kubernetes clusters, Terraform infrastructure-as-code, and automated Python script deployment pipelines.",
            "skills_heading": "Technical Capabilities",
            "skills": ["AWS", "Kubernetes", "Docker", "Terraform", "Ansible", "Python", "Bash", "CI/CD", "Jenkins", "Prometheus", "Grafana", "Linux Administration"],
            "exp_heading": "Employment History",
            "experience": [
                {
                    "role": "Lead DevOps Engineer",
                    "company": "CloudSphere Inc.",
                    "dates": "Oct 2021 - Present",
                    "location": "Seattle, WA",
                    "bullets": [
                        "Managed multi-cluster Kubernetes deployments on AWS EKS serving 10M+ daily active users.",
                        "Implemented Terraform modules for IaC, reducing environment provisioning time from days to 15 minutes.",
                        "Built Python automation tools for automated security compliance scanning and cost optimization."
                    ]
                },
                {
                    "role": "Senior Systems Engineer",
                    "company": "Infrastructure Solutions",
                    "dates": "Jul 2017 - Sep 2021",
                    "location": "Bellevue, WA",
                    "bullets": [
                        "Configured Jenkins CI/CD pipelines for automated testing, artifact creation, and zero-downtime deployment.",
                        "Monitored system health and uptime using Prometheus and Grafana dashboards."
                    ]
                }
            ],
            "edu_heading": "Education Background",
            "education": [
                {
                    "degree": "Master of Science in Computer Science",
                    "institution": "University of Washington",
                    "year": "2015 - 2017"
                },
                {
                    "degree": "Bachelor of Technology in Information Technology",
                    "institution": "IIT Delhi",
                    "year": "2011 - 2015"
                }
            ]
        },
        {
            "id": "resume_05_jordan_lee",
            "layout": "classic",
            "name": "Jordan Lee",
            "title": "Senior Frontend Engineer",
            "contacts": ["jordan.lee@designcode.com", "(617) 555-4321", "Boston, MA"],
            "summary_heading": "Profile",
            "summary": "Creative Frontend Engineer with 4 years of experience specializing in React, Next.js, TypeScript, and state management. Passionate about web performance optimization, accessibility standards (WCAG), and responsive design systems.",
            "skills_heading": "Key Competencies",
            "skills": ["React", "Next.js", "TypeScript", "JavaScript", "HTML5", "CSS3", "Sass", "Redux", "Figma", "Jest", "Web Accessibility", "Webpack"],
            "exp_heading": "Experience Timeline",
            "experience": [
                {
                    "role": "Senior Frontend Developer",
                    "company": "ProductLab Inc.",
                    "dates": "May 2022 - Present",
                    "location": "Boston, MA",
                    "bullets": [
                        "Spearheaded redesign of core web platform using Next.js and TypeScript, boosting Lighthouse performance score to 98.",
                        "Created modular component library used by 20+ developers across the company.",
                        "Enforced WCAG 2.1 AA accessibility compliance across all customer-facing applications."
                    ]
                },
                {
                    "role": "UI Web Developer",
                    "company": "Creative Interactive Studio",
                    "dates": "Jan 2020 - Apr 2022",
                    "location": "Boston, MA",
                    "bullets": [
                        "Developed dynamic single-page applications using React, Redux, and REST API integrations."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "B.A. in Graphic Design & Web Media",
                    "institution": "Rhode Island School of Design",
                    "year": "2016 - 2020"
                }
            ]
        },
        {
            "id": "resume_06_elena_rostova",
            "layout": "modern_header",
            "name": "Elena Rostova",
            "title": "Principal Backend Java & Spring Engineer",
            "contacts": ["elena.rostova@enterprise.dev", "+1 (212) 555-8833", "New York, NY", "linkedin.com/in/elenarostova-dev"],
            "summary_heading": "Summary of Qualifications",
            "summary": "Senior Backend Developer with 8 years of enterprise software engineering experience architecting distributed microservices in Java, Spring Boot, Kafka, and Oracle/PostgreSQL. Specialist in financial transaction processing and high-availability systems.",
            "skills_heading": "Technical Expertise",
            "skills": ["Java", "Spring Boot", "Spring Cloud", "Kafka", "Microservices", "Oracle DB", "PostgreSQL", "Redis", "Docker", "JUnit", "REST Services"],
            "exp_heading": "Professional History",
            "experience": [
                {
                    "role": "Lead Backend Architect",
                    "company": "FinTech Global Services",
                    "dates": "Nov 2021 - Present",
                    "location": "New York, NY",
                    "bullets": [
                        "Led architecture for event-driven payment processing backend using Java 17, Spring Boot 3, and Apache Kafka.",
                        "Handled high transaction volumes of over 50,000 requests/sec with sub-50ms latency.",
                        "Mentored team of 8 backend engineers on best practices, code reviews, and microservice design patterns."
                    ]
                },
                {
                    "role": "Senior Java Developer",
                    "company": "Enterprise Systems Corp",
                    "dates": "Aug 2018 - Oct 2021",
                    "location": "New York, NY",
                    "bullets": [
                        "Developed scalable enterprise web services using Spring MVC, Hibernate, and Oracle database."
                    ]
                },
                {
                    "role": "Software Engineer",
                    "company": "Core Bank Tech",
                    "dates": "Jun 2016 - Jul 2018",
                    "location": "Jersey City, NJ",
                    "bullets": [
                        "Maintained banking portal backend APIs and conducted automated integration testing using JUnit and Mockito."
                    ]
                }
            ],
            "edu_heading": "Academic Background",
            "education": [
                {
                    "degree": "Master of Science in Software Engineering",
                    "institution": "Columbia University",
                    "year": "2014 - 2016"
                }
            ]
        },
        {
            "id": "resume_07_marcus_johnson",
            "layout": "classic",
            "name": "Dr. Marcus Johnson",
            "title": "Senior Data Scientist & NLP Specialist",
            "contacts": ["marcus.johnson@ai-labs.org", "(650) 555-9123", "Palo Alto, CA", "github.com/marcusj-ai"],
            "summary_heading": "Professional Summary",
            "summary": "Accomplished Data Scientist with a PhD and 4 years of industry experience developing machine learning models, natural language processing (NLP) pipelines, and predictive algorithms in Python using PyTorch, Scikit-Learn, and HuggingFace.",
            "skills_heading": "Skills & Expertise",
            "skills": ["Python", "Machine Learning", "Deep Learning", "NLP", "Scikit-Learn", "PyTorch", "TensorFlow", "HuggingFace", "SQL", "Pandas", "LLMs", "MLOps"],
            "exp_heading": "Research & Industry Experience",
            "experience": [
                {
                    "role": "Senior Machine Learning Scientist",
                    "company": "Intelligence AI Labs",
                    "dates": "Aug 2022 - Present",
                    "location": "Palo Alto, CA",
                    "bullets": [
                        "Built custom domain-specific Large Language Models (LLMs) and fine-tuned BERT models for document extraction.",
                        "Designed Python ML pipelines with PyTorch and Scikit-Learn, improving classification accuracy by 22%.",
                        "Deployed containerized model APIs using FastAPI and Triton Inference Server on AWS."
                    ]
                },
                {
                    "role": "Data Scientist",
                    "company": "Analytics Corp",
                    "dates": "Jun 2020 - Jul 2022",
                    "location": "Mountain View, CA",
                    "bullets": [
                        "Developed predictive churn models and customer sentiment analysis algorithms using Python, Pandas, and NLTK."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "Ph.D. in Computer Science (Data Science Focus)",
                    "institution": "University of California, Berkeley",
                    "year": "2016 - 2020"
                }
            ]
        },
        {
            "id": "resume_08_sarah_jenkins",
            "layout": "modern_header",
            "name": "Sarah Jenkins",
            "title": "Technical Product Manager & Agile Coach",
            "contacts": ["s.jenkins@productmindset.com", "(303) 555-6543", "Denver, CO", "linkedin.com/in/sarahjenkins-pm"],
            "summary_heading": "Executive Profile",
            "summary": "Strategic Technical Product Manager with 6 years of experience driving cross-functional software teams, defining product roadmaps, and delivering SaaS solutions. Deep technical background with hands-on Python and SQL skills.",
            "skills_heading": "Core Strengths",
            "skills": ["Product Strategy", "Agile / Scrum", "JIRA", "Roadmap Planning", "User Research", "Python", "SQL", "Data Analytics", "A/B Testing", "Sprint Planning"],
            "exp_heading": "Professional Experience",
            "experience": [
                {
                    "role": "Technical Product Manager",
                    "company": "SaaS Scale Inc.",
                    "dates": "Sep 2021 - Present",
                    "location": "Denver, CO",
                    "bullets": [
                        "Led product lifecycle for B2B analytics platform from concept to launch, achieving $4M ARR in first year.",
                        "Wrote detailed user stories, acceptance criteria, and API specifications for engineering teams.",
                        "Analyzed user engagement data using SQL and Python to guide feature prioritization."
                    ]
                },
                {
                    "role": "Associate Product Manager / Scrum Master",
                    "company": "DevStudio Tech",
                    "dates": "Feb 2018 - Aug 2021",
                    "location": "Boulder, CO",
                    "bullets": [
                        "Facilitated daily standups, sprint planning, and retrospectives for 3 development teams."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "Master of Business Administration (MBA)",
                    "institution": "University of Colorado Boulder",
                    "year": "2016 - 2018"
                },
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "Purdue University",
                    "year": "2012 - 2016"
                }
            ]
        },
        {
            "id": "resume_09_liam_oconnor",
            "layout": "classic",
            "name": "Liam O'Connor",
            "title": "Cross-Platform Mobile Engineer",
            "contacts": ["liam.oconnor@mobileapps.co", "(415) 555-3142", "San Francisco, CA"],
            "summary_heading": "Summary",
            "summary": "Mobile Application Engineer with 3 years of experience building cross-platform iOS and Android mobile applications using Flutter, Dart, Swift, and RESTful APIs. Experience integrating backend services written in Python.",
            "skills_heading": "Skills & Technologies",
            "skills": ["Flutter", "Dart", "Swift", "iOS Development", "Android", "Kotlin", "REST APIs", "GraphQL", "Firebase", "State Management", "Python"],
            "exp_heading": "Work History",
            "experience": [
                {
                    "role": "Mobile Application Engineer",
                    "company": "AppFactory Innovations",
                    "dates": "Apr 2022 - Present",
                    "location": "San Francisco, CA",
                    "bullets": [
                        "Developed multi-platform Flutter mobile applications for fintech clients with 100k+ downloads on App Store & Google Play.",
                        "Integrated secure biometric authentication, offline sync, and real-time push notifications.",
                        "Worked closely with Python backend engineers to define REST and GraphQL API contracts."
                    ]
                },
                {
                    "role": "Junior Mobile Developer",
                    "company": "Startup Mobile Studio",
                    "dates": "Feb 2021 - Mar 2022",
                    "location": "Oakland, CA",
                    "bullets": [
                        "Built native iOS UI components in Swift and assisted in Dart/Flutter migration."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "B.S. in Computer Science",
                    "institution": "University of California, San Diego",
                    "year": "2017 - 2021"
                }
            ]
        },
        {
            "id": "resume_10_zoe_patel",
            "layout": "modern_header",
            "name": "Zoe Patel",
            "title": "Cybersecurity & Automation Engineer",
            "contacts": ["zoe.patel@secnet.io", "(206) 555-8712", "Seattle, WA", "linkedin.com/in/zoepatel-sec"],
            "summary_heading": "Professional Summary",
            "summary": "Cybersecurity Analyst and Automation Specialist with 2.5 years of experience monitoring network threats, conducting vulnerability assessments, and writing Python security scripts for automated log analysis.",
            "skills_heading": "Technical Capabilities",
            "skills": ["Cybersecurity", "Python", "Linux Administration", "Wireshark", "SIEM", "Penetration Testing", "Network Security", "Bash Scripting", "OWASP", "Cloud Security"],
            "exp_heading": "Work History",
            "experience": [
                {
                    "role": "Security Operations Analyst",
                    "company": "SecureCloud Inc.",
                    "dates": "Mar 2023 - Present",
                    "location": "Seattle, WA",
                    "bullets": [
                        "Monitored security event logs across AWS cloud instances using Splunk and SIEM dashboards.",
                        "Wrote custom Python scripts to automate threat intelligence IP lookup and incident triage, cutting response time by 60%.",
                        "Performed regular vulnerability scans using Nessus and coordinated patch management with DevOps teams."
                    ]
                },
                {
                    "role": "Junior Security Analyst",
                    "company": "CyberGuard Security",
                    "dates": "Feb 2022 - Feb 2023",
                    "location": "Tacoma, WA",
                    "bullets": [
                        "Analyzed malware samples, reviewed firewall rules, and conducted internal phishing simulation campaigns."
                    ]
                }
            ],
            "edu_heading": "Education",
            "education": [
                {
                    "degree": "Bachelor of Science in Cybersecurity & Information Assurance",
                    "institution": "Western Governors University",
                    "year": "2018 - 2022"
                }
            ]
        }
    ]

    for candidate in candidates:
        filepath = os.path.join(output_dir, f"{candidate['id']}.pdf")
        build_pdf_resume(filepath, candidate, layout_style=candidate.get("layout", "classic"))
        print(f"Generated: {filepath}")

if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "./data/resumes"
    generate_all_sample_resumes(target_dir)
