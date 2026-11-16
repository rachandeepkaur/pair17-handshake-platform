#!/usr/bin/env python3
"""Populate the Handshake MongoDB database with deterministic demo data.

Run from the repository root (MONGO_URI / MONGO_DB from the environment or .env):
    python backend/db/seed/generate_seed.py

The random draws are the same as the Lab 1 MySQL generator, so the same SEED
produces the same companies, students, jobs, applications, and events.

Use --reset only when it is acceptable to delete all application data first.
"""

import argparse
import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path



BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.mongo import encode, ensure_indexes, get_database, set_counter_floor, utcnow  # noqa: E402


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
# Collections the generator owns; --reset clears them (assistant memory included,
# since it describes these students).
RESET_COLLECTIONS = [
    "accounts", "students", "companies", "company_members", "team_invitations", "preferences",
    "jobs", "applications", "events", "registrations", "saved_items", "message_threads", "messages",
    "sessions", "activity_logs", "conversations", "student_memory", "counters",
]
REQUIRED_EMPTY = ("accounts", "students", "companies", "jobs", "applications", "events", "registrations")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing application data before generating seed data.",
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


def ensure_empty_database(db, reset: bool) -> None:
    has_data = any(db[name].estimated_document_count() for name in REQUIRED_EMPTY)
    if has_data and not reset:
        raise RuntimeError("Database already contains data. Re-run with --reset to replace it.")
    if reset:
        for name in RESET_COLLECTIONS:
            db[name].delete_many({})


class Ids:
    """Sequential integer ids per collection (the counters are set once at the end)."""

    def __init__(self):
        self.last: dict[str, int] = {}

    def next(self, collection: str) -> int:
        self.last[collection] = self.last.get(collection, 0) + 1
        return self.last[collection]


def new_account(ids: Ids, now: datetime, *, email: str, role: str) -> dict:
    return {"_id": ids.next("accounts"), "email": email, "password_hash": DEMO_PASSWORD_HASH, "role": role, "created_at": now}


def generate_companies(db, ids: Ids, cities: list[str]) -> list[dict]:
    now = utcnow()
    accounts, companies, owners = [], [], []
    for index in range(COMPANY_COUNT):
        account = new_account(ids, now, email=f"company{index + 1:03d}@seed.p17.example", role="company")
        accounts.append(account)
        company_name = COMPANY_NAMES[index]
        city = cities[index % len(cities)]
        companies.append(
            {
                "_id": account["_id"],
                "account_id": account["_id"],
                "company_name": company_name,
                "location": f"{city}, CA",
                "description": f"{company_name} connects early-career talent with meaningful work.",
                "contact_info": f"recruiting{index + 1:03d}@seed.p17.example",
                "profile_picture_path": None,
                "updated_at": now,
            }
        )
        owners.append(
            {
                "_id": ids.next("company_members"),
                "company_id": account["_id"],
                "account_id": account["_id"],
                "name": f"{company_name} Recruiting",
                "role": "owner",
                "last_active_at": None,
                "created_at": now,
            }
        )
    db.accounts.insert_many(accounts)
    db.companies.insert_many(companies)
    db.company_members.insert_many(owners)
    return companies


def generate_students(db, ids: Ids, cities: list[str], rng: random.Random) -> tuple[list[int], dict[int, str]]:
    now = utcnow()
    student_ids: list[int] = []
    student_majors: dict[int, str] = {}
    accounts, students = [], []

    for index in range(STUDENT_COUNT):
        account = new_account(ids, now, email=f"student{index + 1:03d}@seed.p17.example", role="student")
        accounts.append(account)
        account_id = account["_id"]
        major = MAJORS[index % len(MAJORS)]
        degree = degree_for_student(index, major)
        student_ids.append(account_id)
        student_majors[account_id] = major
        students.append(
            encode(
                {
                    "_id": account_id,
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
                    "cgpa": Decimal(str(round(rng.uniform(2.7, 4.0), 2))),
                    "experience": f"Completed project work and coursework in {major}.",
                    "phone": f"408-555-{index + 1000:04d}",
                    "skills": SKILL_SETS[index % len(SKILL_SETS)],
                    "profile_picture_path": None,
                    "updated_at": now,
                }
            )
        )
    db.accounts.insert_many(accounts)
    db.students.insert_many(students)
    return student_ids, student_majors


def generate_jobs(db, ids: Ids, companies: list[dict], cities: list[str], rng: random.Random) -> list[dict]:
    today = date.today()
    now = utcnow()
    jobs = []
    for index in range(JOB_COUNT):
        title, category, skills = JOB_TEMPLATES[index % len(JOB_TEMPLATES)]
        active = index < 270
        posting_date = today - timedelta(days=rng.randint(1, 45))
        deadline = today + timedelta(days=rng.randint(7, 90)) if active else today - timedelta(days=rng.randint(1, 30))
        city = cities[index % len(cities)]
        company = companies[index % len(companies)]
        jobs.append(
            encode(
                {
                    "_id": ids.next("jobs"),
                    "company_id": company["_id"],
                    "company_name": company["company_name"],
                    "title": title,
                    "description": f"Join our team as a {title}. You will contribute to practical projects and learn from experienced mentors.",
                    "category": category,
                    "city": city,
                    "location": f"{city}, CA",
                    "is_remote": index % 5 == 0,
                    "salary": Decimal(22_000 + (index % 12) * 7_500),
                    "skills_required": skills,
                    "posting_date": posting_date,
                    "deadline": deadline,
                    "created_at": now,
                }
            )
        )
    db.jobs.insert_many(jobs)
    return jobs


def generate_applications(db, ids: Ids, student_ids: list[int], jobs: list[dict], rng: random.Random) -> None:
    combinations = rng.sample(range(len(student_ids) * len(jobs)), APPLICATION_COUNT)
    statuses = ["Pending", "Pending", "Reviewed", "Declined"]
    applied_at = datetime.combine(date.today() - timedelta(days=3), time(10, 0))
    rows = []
    for combination in combinations:
        student_index, job_index = divmod(combination, len(jobs))
        job = jobs[job_index]
        when = applied_at - timedelta(days=rng.randint(0, 120))
        rows.append(
            {
                "_id": ids.next("applications"),
                "student_id": student_ids[student_index],
                "job_id": job["_id"],
                "company_id": job["company_id"],
                "status": rng.choice(statuses),
                "resume": {
                    "path": f"seed/resumes/student-{student_index + 1:03d}.pdf",
                    "original_filename": f"student-{student_index + 1:03d}.pdf",
                    "size_bytes": None,
                    "sha256": None,
                    "content_type": "application/pdf",
                    "uploaded_at": when,
                },
                "applied_at": when,
                "updated_at": when,
            }
        )
    db.applications.insert_many(rows)


def generate_events(db, ids: Ids, companies: list[dict], cities: list[str]) -> list[dict]:
    today = date.today()
    now = utcnow()
    eligibility_values = [None, "Everyone", "All majors", "Computer Science", "Data Science", "Computer Science, Data Science"]
    events = []
    for index in range(EVENT_COUNT):
        event_name = EVENT_TEMPLATES[index % len(EVENT_TEMPLATES)]
        company = companies[index % len(companies)]
        city = cities[index % len(cities)]
        events.append(
            encode(
                {
                    "_id": ids.next("events"),
                    "company_id": company["_id"],
                    "company_name": company["company_name"],
                    "name": f"{event_name} {index + 1}",
                    "description": f"Meet recruiters and learn about opportunities at this {event_name.lower()}.",
                    "event_date": today + timedelta(days=1 + index % 120),
                    "event_time": time(9 + index % 8, 30 if index % 2 else 0),
                    "location": f"{city}, CA",
                    "eligibility": eligibility_values[index % len(eligibility_values)],
                    "created_at": now,
                }
            )
        )
    db.events.insert_many(events)
    return events


def eligible_for_event(eligibility: str | None, major: str) -> bool:
    if not eligibility or eligibility.casefold() in {"everyone", "all", "all majors"}:
        return True
    allowed = {value.strip().casefold() for value in eligibility.split(",")}
    return major.casefold() in allowed


def generate_registrations(
    db, ids: Ids, events: list[dict], student_ids: list[int], student_majors: dict[int, str], rng: random.Random
) -> None:
    now = utcnow()
    rows = []
    for event in events:
        eligible_students = [s for s in student_ids if eligible_for_event(event["eligibility"], student_majors[s])]
        for student_id in rng.sample(eligible_students, k=min(6, len(eligible_students))):
            rows.append(
                {
                    "_id": ids.next("registrations"),
                    "student_id": student_id,
                    "event_id": event["_id"],
                    "company_id": event["company_id"],
                    "registered_at": now,
                }
            )
    db.registrations.insert_many(rows)


def report_counts(db) -> None:
    print("Seed data created:")
    for name in ("companies", "students", "jobs", "applications", "events", "registrations"):
        print(f"  {name}: {db[name].count_documents({})}")
    print(f"\nAll generated accounts use password: {DEMO_PASSWORD}")
    print("Example student login: student001@seed.p17.example")
    print("Example company login: company001@seed.p17.example")


def main() -> None:
    args = parse_args()
    cities = configured_cities()
    rng = random.Random(settings.seed)
    db = get_database()

    ensure_empty_database(db, args.reset)
    ensure_indexes(db)
    ids = Ids()
    companies = generate_companies(db, ids, cities)
    student_ids, student_majors = generate_students(db, ids, cities, rng)
    jobs = generate_jobs(db, ids, companies, cities, rng)
    generate_applications(db, ids, student_ids, jobs, rng)
    events = generate_events(db, ids, companies, cities)
    generate_registrations(db, ids, events, student_ids, student_majors, rng)
    for collection in ids.last:
        set_counter_floor(db, collection)
    # Assistant layers: the rules, and the long learned memory used by the consolidation demo.
    from db.seed.assistant_memory import seed_assistant_rules, seed_demo_memory

    seed_assistant_rules(db)
    seed_demo_memory(db)
    report_counts(db)


if __name__ == "__main__":
    main()
