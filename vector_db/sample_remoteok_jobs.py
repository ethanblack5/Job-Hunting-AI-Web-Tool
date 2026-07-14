"""
Real sample job postings pulled from https://remoteok.com/api on 2026-07-12.

"""

import re


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


RAW_SAMPLE_JOBS = [
    {
        "job_id": "1134742",
        "title": "Interface Designer",
        "company": "Grow the Roses",
        "tags": ["design", "designer", "web dev", "mobile", "front end", "css", "html"],
        "location": "Only",
        "apply_url": "https://remoteOK.com/remote-jobs/remote-interface-designer-grow-the-roses-1134742",
        "remoteok_url": "https://remoteOK.com/remote-jobs/remote-interface-designer-grow-the-roses-1134742",
        "date_posted": "2026-07-12",
        "min_salary": 0,
        "max_salary": 0,
        "desc": strip_html(
            "We are looking for a talented Interface Designer to create intuitive, "
            "visually engaging, and user-friendly digital experiences. You will work "
            "closely with UX designers, developers, and product teams to design "
            "interfaces that enhance usability and elevate brand identity. Requires "
            "proficiency in Figma, Sketch, or Adobe XD, strong understanding of UI/UX "
            "principles, typography, and visual hierarchy, and experience with "
            "responsive and mobile-first design."
        ),
    },
    {
        "job_id": "1134719",
        "title": "Healthcare Intake Coordinator Alberta",
        "company": "Carewell",
        "tags": ["content writing", "non tech", "teaching", "customer support",
                  "education", "marketing", "strategy", "full time", "coordinator", "medical"],
        "location": "Alberta",
        "apply_url": "https://remoteOK.com/remote-jobs/remote-healthcare-intake-coordinator-alberta-carewell-1134719",
        "remoteok_url": "https://remoteOK.com/remote-jobs/remote-healthcare-intake-coordinator-alberta-carewell-1134719",
        "date_posted": "2026-07-11",
        "min_salary": 0,
        "max_salary": 0,
        "desc": strip_html(
            "Carewell is a category-defining health services business dedicated to "
            "providing coordinated intake support for patients and families."
        ),
    },
    {
        "job_id": "1134710",
        "title": "CRM & Lifecycle Manager",
        "company": "Joko",
        "tags": ["exec", "design", "sys admin", "teaching", "technical", "testing",
                  "marketing", "dev", "virtual assistant", "quality assurance",
                  "mobile", "ops", "engineer", "full time", "digital nomad"],
        "location": "Paris",
        "apply_url": "https://remoteOK.com/remote-jobs/remote-crm-lifecycle-manager-joko-1134710",
        "remoteok_url": "https://remoteOK.com/remote-jobs/remote-crm-lifecycle-manager-joko-1134710",
        "date_posted": "2026-07-11",
        "min_salary": 43400,
        "max_salary": 69300,
        "desc": strip_html(
            "As CRM & Lifecycle Manager, your mission is to design and run lifecycle "
            "programs that turn new signups into engaged, loyal, high-LTV Joko users. "
            "You will own the end-to-end CRM strategy across in-app, push, and email. "
            "5+ years of experience in B2C CRM or lifecycle marketing required, hands-on "
            "with modern CRM platforms (Braze, Iterable, Customer.io)."
        ),
    },
    {
        "job_id": "1134707",
        "title": "Graduate Data Scientist",
        "company": "Work Force Nexus",
        "tags": ["data science"],
        "location": "Australia",
        "apply_url": "https://remoteOK.com/remote-jobs/remote-graduate-data-scientist-work-force-nexus-1134707",
        "remoteok_url": "https://remoteOK.com/remote-jobs/remote-graduate-data-scientist-work-force-nexus-1134707",
        "date_posted": "2026-07-11",
        "min_salary": 0,
        "max_salary": 0,
        "desc": strip_html(
            "Job Title: Graduate Data Scientist. Location: Australia (Remote). "
            "Employment Type: Full-Time."
        ),
    },
    {
        "job_id": "1134749",
        "title": "Billing Specialist",
        "company": "DataBank",
        "tags": ["exec", "strategy", "customer support", "testing", "content writing",
                  "marketing", "medical", "finance", "python", "education", "cloud",
                  "engineer", "digital nomad", "accounting", "excel"],
        "location": "Dallas",
        "apply_url": "https://remoteOK.com/remote-jobs/remote-billing-specialist-databank-1134749",
        "remoteok_url": "https://remoteOK.com/remote-jobs/remote-billing-specialist-databank-1134749",
        "date_posted": "2026-07-10",
        "min_salary": 0,
        "max_salary": 0,
        "desc": strip_html(
            "DataBank is a leading provider of enterprise-class data center, cloud, "
            "and interconnection services. Our billing team is responsible for "
            "processing all billing transactions, resolving disputes, and assisting "
            "with collections. Requires 1-5 years billing/collections experience and "
            "intermediate to advanced Excel skills."
        ),
    },
    {
        "job_id": "1134741",
        "title": "Educational Programs Administrator",
        "company": "Lingraphica",
        "tags": ["design", "teaching", "education", "designer", "technical",
                  "customer support", "medical", "consulting", "sales", "admin", "speech"],
        "location": "Princeton, New Jersey, United States",
        "apply_url": "https://remoteOK.com/remote-jobs/remote-educational-programs-administrator-lingraphica-1134741",
        "remoteok_url": "https://remoteOK.com/remote-jobs/remote-educational-programs-administrator-lingraphica-1134741",
        "date_posted": "2026-07-10",
        "min_salary": 50000,
        "max_salary": 55000,
        "desc": strip_html(
            "Lingraphica provides speech-generating devices to help improve "
            "communication for people with communication impairments. The Educational "
            "Programs Administrator manages logistics for training demos and university "
            "webinars, schedules SLP device demonstrations, and coordinates device "
            "shipments."
        ),
    },
]
