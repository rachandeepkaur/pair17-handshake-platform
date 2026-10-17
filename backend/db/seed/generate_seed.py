#!/usr/bin/env python3
"""Populate the Handshake database with deterministic Lab 1 demo data.

Run from the repository root after applying schema.sql:
    python backend/db/seed/generate_seed.py

Use --reset only when it is acceptable to delete all application data first.
"""

import argparse
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text


BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402


COMPANY_COUNT = 50
STUDENT_COUNT = 200
JOB_COUNT = 300
APPLICATION_COUNT = 1_500
EVENT_COUNT = 100
DEMO_PASSWORD = "SeedPass17!"
# bcrypt hash for DEMO_PASSWORD. Keeping it fixed makes generated rows reproducible.
DEMO_PASSWORD_HASH = "$2b$12$BKu0SmcY/TbimesAkS30IOBrJEroacn/tsGRmNtK.XKuRjMXpQxuu"

MAJORS = [
    "Computer Science",
    "Data Science",
    "Software Engineering",
    "Information Systems",
    "Business Administration",
    "Electrical Engineering",
    "Mathematics",
    "Design Studies",
]
UNDERGRADUATE_DEGREES = {
    "Computer Science": "Bachelor of Science in Computer Science",
    "Data Science": "Bachelor of Science in Data Science",
    "Software Engineering": "Bachelor of Science in Software Engineering",
    "Information Systems": "Bachelor of Science in Information Systems",
    "Business Administration": "Bachelor of Business Administration",
    "Electrical Engineering": "Bachelor of Science in Electrical Engineering",
    "Mathematics": "Bachelor of Science in Mathematics",
    "Design Studies": "Bachelor of Fine Arts in Design Studies",
}
GRADUATE_DEGREES = {
    "Computer Science": "Master of Science in Computer Science",
    "Data Science": "Master of Science in Data Science",
    "Software Engineering": "Master of Science in Software Engineering",
    "Information Systems": "Master of Science in Information Systems",
    "Business Administration": "Master of Business Administration",
    "Electrical Engineering": "Master of Science in Electrical Engineering",
    "Mathematics": "Master of Science in Mathematics",
    "Design Studies": "Master of Fine Arts in Design Studies",
}
# One graduate student for each major keeps the 200-record demo set varied but realistic.
GRADUATE_STUDENT_INDICES = {16, 25, 34, 43, 52, 61, 70, 79}
STUDENT_NAMES = [

    "Lorelai Gilmore", "Rory Gilmore", "Emily Gilmore", "Richard Gilmore", "Luke Danes",
    "Sookie St. James", "Lane Kim", "Paris Geller", "Dean Forester", "Jess Mariano",
    "Logan Huntzberger", "Michel Gerard", "Kirk Gleason", "Taylor Doose", "April Nardini",

    "Serena van der Woodsen", "Blair Waldorf", "Chuck Bass", "Nate Archibald", "Dan Humphrey",
    "Jenny Humphrey", "Vanessa Abrams", "Georgina Sparks", "Lily van der Woodsen", "Rufus Humphrey",
    "Eleanor Waldorf", "Cyrus Rose", "Dorota Kishlovsky", "Eric van der Woodsen", "Carter Baizen",

    "Richard Hendricks", "Erlich Bachman", "Jared Dunn", "Dinesh Chugtai", "Bertram Gilfoyle",
    "Monica Hall", "Gavin Belson", "Nelson Bighetti", "Laurie Bream", "Peter Gregory",
    "Russ Hanneman", "Carla Walton",

    "Rachel Green", "Monica Geller", "Phoebe Buffay", "Joey Tribbiani", "Chandler Bing",
    "Ross Geller", "Janice Litman-Goralnik", "Mike Hannigan", "Carol Willick", "Emma Geller-Green",

    "Ted Mosby", "Robin Scherbatsky", "Marshall Eriksen", "Lily Aldrin", "Barney Stinson",
    "Tracy McConnell", "Ranjit Singh", "Zoey Pierson", "Quinn Garvey", "Nora Zinman",

    "Jessica Day", "Nick Miller", "Winston Bishop", "Cecilia Parekh", "Aly Nelson",
    "Reagan Lucas", "Nadia Shapiro", "Fawn Moscato", "Robby McFerrin", "Sadie Campbell",

    "Ginny Miller", "Georgia Miller", "Austin Miller", "Marcus Baker", "Maxine Baker",
    "Paul Randolph", "Zion Miller", "Abby Littman", "Hunter Chen", "Sophie Sanchez",

    "Aria Montgomery", "Spencer Hastings", "Hanna Marin", "Emily Fields", "Alison DiLaurentis",
    "Mona Vanderwaal", "Ezra Fitz", "Caleb Rivers", "Toby Cavanaugh", "Ashley Marin",
    "Ella Montgomery", "Jason DiLaurentis",

    "Sheldon Cooper", "Leonard Hofstadter", "Penny Hofstadter", "Howard Wolowitz", "Raj Koothrappali",
    "Amy Farrah Fowler", "Bernadette Rostenkowski", "Stuart Bloom", "Leslie Winkle", "Beverly Hofstadter",

    "Mary Cooper", "George Cooper", "Georgie Cooper", "Missy Cooper", "Connie Tucker",
    "Mandy McAllister", "Paige Swanson", "Tam Nguyen", "Billy Sparks", "Brenda Sparks",

    "Shaun Murphy", "Claire Browne", "Aaron Glassman", "Audrey Lim", "Morgan Reznick",
    "Alex Park", "Jared Kalu", "Neil Melendez", "Marcus Andrews", "Lea Dilallo",
    "Jordan Allen", "Asher Wolke", "Dalisay Villanueva",

    "Frankie Heck", "Mike Heck", "Axl Heck", "Sue Heck", "Brick Heck",
    "Bob Pat Spence", "Nancy Donahue", "Brad Bottig", "Sean Donahue", "Lexie Brooks",

    "Devi Vishwakumar", "Ben Gross", "Paxton Hall-Yoshida", "Eleanor Wong", "Fabiola Torres",
    "Nalini Vishwakumar", "Kamala Nandiwadal", "Mohan Vishwakumar", "Aneesa Qureshi", "Trent Harrison",
    "Desmond Franklin", "Margot Ramos",

    "Isabel Conklin", "Conrad Fisher", "Jeremiah Fisher", "Steven Conklin", "Taylor Jewel",
    "Laurel Park", "Susannah Fisher", "Cam Cameron", "Cleveland Castillo", "John Conklin",

    "Erin Quinn", "Orla McCool", "Clare Devlin", "Michelle Mallon", "James Maguire",
    "Sister Michael", "Gerry Quinn", "Mary Quinn", "Joe McCool", "Sarah McCool",

    "Johnny Rose", "Moira Rose", "David Rose", "Alexis Rose", "Stevie Budd",
    "Roland Schitt", "Jocelyn Schitt", "Mutt Schitt", "Twyla Sands", "Patrick Brewer",
    "Ted Mullens", "Ronnie Lee",

    "Sam Gardner", "Elsa Gardner", "Doug Gardner", "Casey Gardner", "Zahid Raja",
    "Julia Sasaki", "Evan Chapin", "Paige Hardaway", "Izzie Taylor", "Beth Chapin",

    "Daphne Bridgerton", "Simon Basset", "Anthony Bridgerton", "Kate Sharma", "Penelope Featherington",
    "Colin Bridgerton", "Eloise Bridgerton", "Benedict Bridgerton", "Violet Bridgerton",
]
if len(STUDENT_NAMES) != STUDENT_COUNT or len(set(STUDENT_NAMES)) != STUDENT_COUNT:
    raise RuntimeError("STUDENT_NAMES must contain exactly 200 unique names")


def degree_for_student(index: int, major: str) -> str:
    degrees = GRADUATE_DEGREES if index in GRADUATE_STUDENT_INDICES else UNDERGRADUATE_DEGREES
    return degrees[major]


COMPANY_NAMES = [
    "Google", "Apple", "Microsoft", "Amazon", "Meta", "NVIDIA", "Adobe", "Salesforce",
    "Oracle", "Cisco", "Intel", "IBM", "Netflix", "Airbnb", "Uber", "Lyft", "LinkedIn",
    "Stripe", "Block", "PayPal", "Visa", "Mastercard", "JPMorgan Chase", "Goldman Sachs",
    "Morgan Stanley", "Deloitte", "Accenture", "EY", "KPMG", "PwC", "Tesla", "SpaceX",
    "ServiceNow", "Workday", "Zoom", "Databricks", "Snowflake", "Palantir", "Atlassian",
    "Shopify", "Instacart", "DoorDash", "Electronic Arts", "Intuit", "Autodesk", "VMware",
    "Dropbox", "Pinterest", "Reddit", "Figma",
]
COLLEGES = [
    "San Jose State University",
    "Yale University",
    "Stanford University",
    "Columbia University",
    "New York University",
    "Harvard University",
]
SKILL_SETS = [
    "Python, SQL, Pandas, Tableau",
    "JavaScript, React, Node.js, CSS",
    "Java, Spring Boot, MySQL, Docker",
    "Python, Machine Learning, scikit-learn, TensorFlow",
    "Python, Machine Learning, PyTorch, Model Evaluation",
    "Python, Large Language Models, Prompt Engineering, RAG",
    "Python, Agentic AI, Tool Calling, LangChain",
    "Python, NLP, Vector Databases, Embeddings",
    "Figma, User Research, Prototyping, HTML",
    "Excel, SQL, Power BI, Communication",
]
JOB_TEMPLATES = [
    ("Software Engineering Intern", "internship", "Python, React, SQL"),
    ("Data Science Intern", "internship", "Python, SQL, Pandas"),
    ("Machine Learning Intern", "internship", "Python, Machine Learning, PyTorch"),
    ("Agentic AI Intern", "internship", "Python, Agentic AI, Tool Calling"),
    ("LLM Research Intern", "internship", "Python, Large Language Models, Model Evaluation"),
    ("Business Analyst Intern", "internship", "Excel, SQL, Tableau"),
    ("Junior Software Engineer", "full_time", "Java, Spring Boot, MySQL"),
    ("Data Analyst", "full_time", "SQL, Python, Power BI"),
    ("IT Support Assistant", "part_time", "Customer Service, Troubleshooting"),
    ("Research Assistant", "on_campus", "Research, Python, Writing"),
    ("UX Design Intern", "internship", "Figma, User Research, Prototyping"),
]
EVENT_TEMPLATES = [
    "Technology Career Fair",
    "Data Science Networking Night",
    "Software Engineering Resume Workshop",
    "Internship Information Session",
    "Employer Coffee Chat",
    "Career Paths Panel",
]
RESET_TABLES = [
    "messages",
    "conversations",
    "team_invitations",
    "company_members",
    "preferences",
    "saved_items",
    "registrations",
    "applications",
    "events",
    "jobs",
    "students",
    "companies",
    "accounts",
]
REQUIRED_TABLES = {"accounts", "students", "companies", "jobs", "applications", "events", "registrations"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing database application data before generating seed data.",
    )
    return parser.parse_args()


def configured_cities() -> list[str]:
    cities = settings.cities
    invalid_values = {"city_one", "city_two", "city_three"}
    if len(cities) != 3 or len({city.casefold() for city in cities}) != 3 or any(
        city.casefold() in invalid_values for city in cities
    ):
        raise ValueError("CITY_SET must contain the three distinct cities assigned to this pair on Canvas")
    return cities


def table_names(connection) -> set[str]:
    return {row[0] for row in connection.execute(text("SHOW TABLES"))}


def clear_existing_data(connection, tables: set[str]) -> None:
    for table in RESET_TABLES:
        if table in tables:
            connection.execute(text(f"DELETE FROM {table}"))


def ensure_empty_database(connection, tables: set[str], reset: bool) -> None:
    missing = REQUIRED_TABLES - tables
    if missing:
        raise RuntimeError(f"Database schema is missing required tables: {', '.join(sorted(missing))}")

    has_data = any(
        connection.scalar(text(f"SELECT EXISTS(SELECT 1 FROM {table} LIMIT 1)"))
        for table in REQUIRED_TABLES
    )
    if has_data and not reset:
        raise RuntimeError("Database already contains data. Re-run with --reset to replace it.")
    if reset:
        clear_existing_data(connection, tables)


def insert_account(connection, *, email: str, role: str) -> int:
    result = connection.execute(
        text(
            """
            INSERT INTO accounts (email, password_hash, role)
            VALUES (:email, :password_hash, :role)
            """
        ),
        {"email": email, "password_hash": DEMO_PASSWORD_HASH, "role": role},
    )
    return int(result.lastrowid)


def generate_companies(connection, cities: list[str]) -> list[int]:
    company_ids: list[int] = []
    company_rows = []
    owner_rows = []

    for index in range(COMPANY_COUNT):
        account_id = insert_account(
            connection,
            email=f"company{index + 1:03d}@seed.p17.example",
            role="company",
        )
        company_ids.append(account_id)
        company_name = COMPANY_NAMES[index]
        city = cities[index % len(cities)]
        company_rows.append(
            {
                "account_id": account_id,
                "company_name": company_name,
                "location": f"{city}, CA",
                "description": f"{company_name} connects early-career talent with meaningful work.",
                "contact_info": f"recruiting{index + 1:03d}@seed.p17.example",
            }
        )
        owner_rows.append(
            {
                "company_id": account_id,
                "account_id": account_id,
                "name": f"{company_name} Recruiting",
                "role": "owner",
            }
        )

    connection.execute(
        text(
            """
            INSERT INTO companies (account_id, company_name, location, description, contact_info)
            VALUES (:account_id, :company_name, :location, :description, :contact_info)
            """
        ),
        company_rows,
    )
    connection.execute(
        text(
            """
            INSERT INTO company_members (company_id, account_id, name, role)
            VALUES (:company_id, :account_id, :name, :role)
            """
        ),
        owner_rows,
    )
    return company_ids


def generate_students(connection, cities: list[str], rng: random.Random) -> tuple[list[int], dict[int, str]]:
    student_ids: list[int] = []
    student_majors: dict[int, str] = {}
    student_rows = []

    for index in range(STUDENT_COUNT):
        account_id = insert_account(
            connection,
            email=f"student{index + 1:03d}@seed.p17.example",
            role="student",
        )
        major = MAJORS[index % len(MAJORS)]
        degree = degree_for_student(index, major)
        student_ids.append(account_id)
        student_majors[account_id] = major
        student_rows.append(
            {
                "account_id": account_id,
                "name": STUDENT_NAMES[index],
                "college_name": COLLEGES[index % len(COLLEGES)],
                "date_of_birth": date(1999 + index % 6, (index % 12) + 1, (index % 27) + 1),
                "city": cities[index % len(cities)],
                "state": "CA",
                "country": "United States",
                "career_objective": f"Seeking an entry-level opportunity in {major}.",
                "degree": degree,
                "major": major,
                "graduation_year": 2026 + index % 4,
                "cgpa": round(rng.uniform(2.7, 4.0), 2),
                "experience": f"Completed project work and coursework in {major}.",
                "phone": f"408-555-{index + 1000:04d}",
                "skills": SKILL_SETS[index % len(SKILL_SETS)],
            }
        )

    connection.execute(
        text(
            """
            INSERT INTO students (
                account_id, name, college_name, date_of_birth, city, state, country,
                career_objective, degree, major, graduation_year, cgpa, experience, phone, skills
            ) VALUES (
                :account_id, :name, :college_name, :date_of_birth, :city, :state, :country,
                :career_objective, :degree, :major, :graduation_year, :cgpa, :experience, :phone, :skills
            )
            """
        ),
        student_rows,
    )
    return student_ids, student_majors


def generate_jobs(connection, company_ids: list[int], cities: list[str], rng: random.Random) -> list[int]:
    today = date.today()
    job_ids: list[int] = []

    for index in range(JOB_COUNT):
        title, category, skills = JOB_TEMPLATES[index % len(JOB_TEMPLATES)]
        active = index < 270
        posting_date = today - timedelta(days=rng.randint(1, 45))
        deadline = today + timedelta(days=rng.randint(7, 90)) if active else today - timedelta(days=rng.randint(1, 30))
        city = cities[index % len(cities)]
        result = connection.execute(
            text(
                """
                INSERT INTO jobs (
                    company_id, title, description, category, city, location, is_remote,
                    salary, skills_required, posting_date, deadline
                ) VALUES (
                    :company_id, :title, :description, :category, :city, :location, :is_remote,
                    :salary, :skills_required, :posting_date, :deadline
                )
                """
            ),
            {
                "company_id": company_ids[index % len(company_ids)],
                "title": title,
                "description": f"Join our team as a {title}. You will contribute to practical projects and learn from experienced mentors.",
                "category": category,
                "city": city,
                "location": f"{city}, CA",
                "is_remote": index % 5 == 0,
                "salary": 22_000 + (index % 12) * 7_500,
                "skills_required": skills,
                "posting_date": posting_date,
                "deadline": deadline,
            },
        )
        job_ids.append(int(result.lastrowid))
    return job_ids


def generate_applications(connection, student_ids: list[int], job_ids: list[int], rng: random.Random) -> None:
    combinations = rng.sample(range(len(student_ids) * len(job_ids)), APPLICATION_COUNT)
    statuses = ["Pending", "Pending", "Reviewed", "Declined"]
    applied_at = datetime.combine(date.today() - timedelta(days=3), time(10, 0))
    rows = []
    for combination in combinations:
        student_index, job_index = divmod(combination, len(job_ids))
        rows.append(
            {
                "student_id": student_ids[student_index],
                "job_id": job_ids[job_index],
                "resume_path": f"seed/resumes/student-{student_index + 1:03d}.pdf",
                "status": rng.choice(statuses),
                "applied_at": applied_at - timedelta(days=rng.randint(0, 120)),
            }
        )
    connection.execute(
        text(
            """
            INSERT INTO applications (student_id, job_id, resume_path, status, applied_at)
            VALUES (:student_id, :job_id, :resume_path, :status, :applied_at)
            """
        ),
        rows,
    )


def generate_events(connection, company_ids: list[int], cities: list[str]) -> list[tuple[int, str | None]]:
    today = date.today()
    events: list[tuple[int, str | None]] = []
    eligibility_values = [None, "Everyone", "All majors", "Computer Science", "Data Science", "Computer Science, Data Science"]

    for index in range(EVENT_COUNT):
        event_name = EVENT_TEMPLATES[index % len(EVENT_TEMPLATES)]
        eligibility = eligibility_values[index % len(eligibility_values)]
        city = cities[index % len(cities)]
        result = connection.execute(
            text(
                """
                INSERT INTO events (company_id, name, description, event_date, event_time, location, eligibility)
                VALUES (:company_id, :name, :description, :event_date, :event_time, :location, :eligibility)
                """
            ),
            {
                "company_id": company_ids[index % len(company_ids)],
                "name": f"{event_name} {index + 1}",
                "description": f"Meet recruiters and learn about opportunities at this {event_name.lower()}.",
                "event_date": today + timedelta(days=1 + index % 120),
                "event_time": time(9 + index % 8, 30 if index % 2 else 0),
                "location": f"{city}, CA",
                "eligibility": eligibility,
            },
        )
        events.append((int(result.lastrowid), eligibility))
    return events


def eligible_for_event(eligibility: str | None, major: str) -> bool:
    if not eligibility or eligibility.casefold() in {"everyone", "all", "all majors"}:
        return True
    allowed = {value.strip().casefold() for value in eligibility.split(",")}
    return major.casefold() in allowed


def generate_registrations(
    connection,
    events: list[tuple[int, str | None]],
    student_ids: list[int],
    student_majors: dict[int, str],
    rng: random.Random,
) -> None:
    rows = []
    for event_id, eligibility in events:
        eligible_students = [student_id for student_id in student_ids if eligible_for_event(eligibility, student_majors[student_id])]
        for student_id in rng.sample(eligible_students, k=min(6, len(eligible_students))):
            rows.append({"student_id": student_id, "event_id": event_id})
    connection.execute(
        text("INSERT INTO registrations (student_id, event_id) VALUES (:student_id, :event_id)"),
        rows,
    )


def report_counts(connection) -> None:
    print("Seed data created:")
    for table in ("companies", "students", "jobs", "applications", "events", "registrations"):
        count = connection.scalar(text(f"SELECT COUNT(*) FROM {table}"))
        print(f"  {table}: {count}")
    print(f"\nAll generated accounts use password: {DEMO_PASSWORD}")
    print("Example student login: student001@seed.p17.example")
    print("Example company login: company001@seed.p17.example")


def main() -> None:
    args = parse_args()
    cities = configured_cities()
    rng = random.Random(settings.seed)
    engine = create_engine(settings.database_url)

    with engine.begin() as connection:
        tables = table_names(connection)
        ensure_empty_database(connection, tables, args.reset)
        company_ids = generate_companies(connection, cities)
        student_ids, student_majors = generate_students(connection, cities, rng)
        job_ids = generate_jobs(connection, company_ids, cities, rng)
        generate_applications(connection, student_ids, job_ids, rng)
        events = generate_events(connection, company_ids, cities)
        generate_registrations(connection, events, student_ids, student_majors, rng)
        report_counts(connection)


if __name__ == "__main__":
    main()
