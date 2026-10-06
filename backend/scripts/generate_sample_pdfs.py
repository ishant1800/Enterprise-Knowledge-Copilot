import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_docs"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def build_pdf(filename: str, title: str, pages_data: list):
    pdf_path = SAMPLE_DIR / filename
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f766e"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )

    story = []

    for i, page_sections in enumerate(pages_data):
        if i == 0:
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))

        for section_title, content in page_sections:
            story.append(Paragraph(section_title, h2_style))
            for paragraph in content:
                story.append(Paragraph(paragraph, body_style))
            story.append(Spacer(1, 10))

        if i < len(pages_data) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Generated sample PDF: {pdf_path}")


def generate_all():
    # 1. Enterprise AI Security Policy
    ai_security_pages = [
        # Page 1
        [
            ("1. Purpose and Scope", [
                "This document establishes mandatory information security controls for enterprise generative AI, cloud workloads, and data governance. All full-time employees, contractors, and third-party vendors must strictly adhere to these policies.",
                "Compliance audits are conducted quarterly by the Information Security Committee. Non-compliance may lead to access revocation and disciplinary action.",
            ]),
            ("2. Data Classification Levels", [
                "Organizational data is categorized into four strict tiers:",
                "Tier 1 - Public: Marketing brochures, published documentation, public repository code.",
                "Tier 2 - Internal: Internal memos, company-wide announcements, standard org charts.",
                "Tier 3 - Confidential: Customer personally identifiable information (PII), proprietary algorithms, financial ledgers, and trade secrets.",
                "Tier 4 - Restricted: Production cryptographic root keys, PCI DSS cardholder data, executive board minutes, and unreleased M&A agreements.",
            ]),
        ],
        # Page 2
        [
            ("3. Authentication and Credential Management", [
                "All internal user accounts require hardware-backed FIDO2 multi-factor authentication (MFA). Single-factor SMS codes are strictly forbidden for administrative systems.",
                "Password Rotation Policy: Passwords must be a minimum of 16 characters in length, containing uppercase letters, lowercase letters, numbers, and symbols. Passwords must be rotated every 90 days. Account lockouts trigger automatically after 5 consecutive failed login attempts.",
            ]),
            ("4. Acceptable Use of Generative AI Models", [
                "Employees are prohibited from uploading Tier 3 (Confidential) or Tier 4 (Restricted) data into public AI services such as commercial chatbots without signed enterprise business associate agreements.",
                "Enterprise Knowledge Copilot and internal model endpoints operate under private tenant boundary isolation where prompt inputs and retrieved context are never used for model re-training.",
            ]),
        ],
        # Page 3
        [
            ("5. Security Incident Reporting and SLAs", [
                "Any suspected credential breach, unauthorized data exfiltration, or abnormal access spike must be reported to security-ops@enterprise.internal within 15 minutes of detection.",
                "Critical Sev-1 security incidents require an emergency containment team assembly within 30 minutes, with executive status updates broadcasted every 60 minutes until full mitigation.",
            ]),
        ],
    ]

    # 2. Cloud Infrastructure SOP
    cloud_sop_pages = [
        # Page 1
        [
            ("1. Production Deployment Workflow", [
                "All cloud production services are deployed via GitOps declarative pipelines in GitLab CI/CD. Direct manual mutations using cloud console portals are strictly prohibited.",
                "Production releases must undergo static application security testing (SAST), automated unit tests (>85% coverage), and container image vulnerability scans prior to deployment approval.",
                "Every production deployment requires approval from at least two senior code reviewers and an automated sanity run in staging.",
            ]),
            ("2. Canary Release Strategy", [
                "New application versions are deployed using progressive traffic canary routing:",
                "Step 1: Direct 5% of inbound user traffic to the canary pod cluster for 15 minutes.",
                "Step 2: Monitor HTTP 5xx error rate and p99 latency metrics. If error rate remains below 0.05%, advance traffic split to 25%.",
                "Step 3: After 30 minutes of stable metrics, route 100% of production traffic to the new version.",
            ]),
        ],
        # Page 2
        [
            ("3. Automated Rollback Procedures", [
                "Automated rollback triggers immediately if canary error rates exceed 0.2% over a rolling 3-minute window, or if p99 latency exceeds 450 milliseconds.",
                "The CI/CD orchestrator reverts DNS routing to the stable green deployment and drains canary connections within 60 seconds.",
                "Post-rollback, the on-call Site Reliability Engineer must freeze production pipelines and initiate an incident post-mortem within 24 hours.",
            ]),
            ("4. Disaster Recovery Targets (RTO / RPO)", [
                "Recovery Time Objective (RTO): Production core API services must restore normal operations within 60 minutes of catastrophic regional outage.",
                "Recovery Point Objective (RPO): Database transaction logs are continuously replicated across dual regions with maximum permissible data loss window of 5 minutes.",
            ]),
        ],
    ]

    # 3. Employee Remote Work Guide
    remote_work_pages = [
        # Page 1
        [
            ("1. Overview and Core Collaboration Hours", [
                "Enterprise Knowledge Copilot supports a flexible remote-first hybrid work model. Team members may work from home, regional hubs, or approved remote locations.",
                "To maintain synchronization across distributed engineering and product squads, all full-time employees are expected to be available for synchronous collaboration during core hours: 10:00 AM to 3:00 PM Eastern Time (ET), Monday through Thursday.",
            ]),
            ("2. Monthly High-Speed Internet Stipend", [
                "All active remote employees are eligible for a monthly internet connectivity stipend of $75.00 USD.",
                "Stipends are processed automatically via payroll on the final business day of each calendar month. No manual receipt submission is required for the internet stipend.",
            ]),
        ],
        # Page 2
        [
            ("3. Home Office Equipment Reimbursement", [
                "Upon joining, eligible remote staff receive a one-time home office setup reimbursement budget up to $1,200.00 USD.",
                "Qualifying purchases include ergonomic desks, chairs, external 4K monitors, noise-cancelling headphones, and webcams.",
                "Expense receipts must be submitted via the Expensify portal within 60 calendar days of employee start date.",
            ]),
            ("4. Travel and Quarterly Onsites", [
                "All travel expenses for mandatory quarterly engineering summits must be booked using the corporate Navan travel portal at least 21 days in advance.",
                "Meals during travel are reimbursed up to the daily per diem limit of $85.00 USD per day.",
            ]),
        ],
    ]

    build_pdf("Enterprise_AI_Security_Policy.pdf", "Enterprise Information Security Policy", ai_security_pages)
    build_pdf("Cloud_Infrastructure_SOP.pdf", "Cloud Production Infrastructure SOP", cloud_sop_pages)
    build_pdf("Employee_Remote_Work_Guide.pdf", "Employee Remote Work and Benefits Guide", remote_work_pages)


if __name__ == "__main__":
    generate_all()
