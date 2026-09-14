import hashlib
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "SimplifyJobs/Summer2027-Internships/dev/README.md"
)

SEEN_FILE = Path("opportunities.json")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


# Strong evidence that the opportunity targets underclassmen.
STRONG_EARLY_TALENT = [
    "freshman",
    "freshmen",
    "first year",
    "first-year",
    "sophomore",
    "sophomores",
    "second year",
    "second-year",
    "underclassman",
    "underclassmen",
]

# Programs that MAY be designed for early talent.
POSSIBLE_EARLY_TALENT = [
    "early talent",
    "early identification",
    "early insights",
    "early insight",
    "discovery program",
    "explore program",
    "student program",
    "university program",
    "emerging talent",
]


ROLE_CATEGORIES = {
    "💻 Software Engineering": [
        "software engineer",
        "software engineering",
        "software developer",
        "swe",
        "full stack",
        "fullstack",
        "backend",
        "frontend",
        "web developer",
        "mobile engineer",
    ],

    "🤖 AI / Machine Learning": [
        "machine learning",
        "ml engineer",
        "artificial intelligence",
        "ai engineer",
        "computer vision",
        "deep learning",
    ],

    "📊 Data": [
        "data engineer",
        "data scientist",
        "data science",
        "analytics engineer",
    ],

    "🔐 Cybersecurity": [
        "security engineer",
        "cybersecurity",
        "cyber security",
        "information security",
        "security analyst",
    ],

    "☁️ Cloud / Infrastructure": [
        "cloud engineer",
        "platform engineer",
        "devops",
        "site reliability",
        "infrastructure engineer",
    ],

    "⚙️ Systems / Firmware": [
        "firmware",
        "embedded",
        "systems software",
        "kernel",
        "operating systems",
    ],

    "📈 Quant / Trading": [
        "quantitative",
        "quant developer",
        "quant trader",
        "trading",
    ],
}


def get_readme():
    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()
    return response.text


def parse_jobs(readme):
    jobs = []

    soup = BeautifulSoup(readme, "html.parser")

    previous_company = None

    for row in soup.find_all("tr"):
        columns = row.find_all("td")

        if len(columns) < 4:
            continue

        company = columns[0].get_text(" ", strip=True)
        role = columns[1].get_text(" ", strip=True)
        location = columns[2].get_text(", ", strip=True)

        # Simplify uses ↳ when multiple roles belong to the same company.
        if company == "↳":
            company = previous_company
        else:
            previous_company = company

        links = columns[3].find_all("a", href=True)

        if not links:
            continue

        link = links[0]["href"]

        jobs.append({
            "company": company or "Unknown Company",
            "role": role,
            "location": location,
            "link": link,
        })

    return jobs


def get_category(job):
    role = job["role"].lower()

    for category, keywords in ROLE_CATEGORIES.items():
        if any(keyword in role for keyword in keywords):
            return category

    return "🌱 General Early Talent"


def classify_early_talent(job):
    text = f"{job['company']} {job['role']}".lower()

    for keyword in STRONG_EARLY_TALENT:
        if keyword in text:
            return "strong", keyword

    for keyword in POSSIBLE_EARLY_TALENT:
        if keyword in text:
            return "possible", keyword

    return None, None


def job_id(job):
    # Remove tracking parameters before hashing.
    clean_link = job["link"].split("?")[0].rstrip("/")

    return hashlib.sha256(
        clean_link.encode("utf-8")
    ).hexdigest()


def load_seen():
    if not SEEN_FILE.exists():
        return set()

    with open(SEEN_FILE, "r") as file:
        return set(json.load(file))


def save_seen(seen):
    with open(SEEN_FILE, "w") as file:
        json.dump(sorted(seen), file, indent=2)


def send_discord(job, confidence, matched_keyword):
    if not WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set.")

    category = get_category(job)

    if confidence == "strong":
        confidence_text = "🎓 Freshman / Sophomore Targeted"
    else:
        confidence_text = "🌱 Possible Early Talent"

    payload = {
        "embeds": [
            {
                "title": "New Early Talent Opportunity",
                "description": (
                    f"**{confidence_text}**\n"
                    f"{category}\n\n"
                    f"**{job['role']}**"
                ),
                "url": job["link"],
                "fields": [
                    {
                        "name": "Company",
                        "value": job["company"],
                        "inline": True,
                    },
                    {
                        "name": "Location",
                        "value": job["location"],
                        "inline": True,
                    },
                    {
                        "name": "Detected From",
                        "value": matched_keyword,
                        "inline": True,
                    },
                    {
                        "name": "Application",
                        "value": f"[Apply Here]({job['link']})",
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": (
                        "Always verify class-year eligibility "
                        "in the application."
                    )
                },
            }
        ]
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()


def main():
    print("Checking for early talent opportunities...")

    readme = get_readme()
    jobs = parse_jobs(readme)

    print(f"Parsed {len(jobs)} total internships.")

    # Parser health check
    if len(jobs) < 50:
        raise RuntimeError(
            f"Only parsed {len(jobs)} jobs. "
            "Simplify's format may have changed."
        )

    matches = []

    for job in jobs:
        confidence, keyword = classify_early_talent(job)

        if confidence:
            matches.append((job, confidence, keyword))

    print(f"Found {len(matches)} early-talent matches.")

    seen = load_seen()

    # Initialize without spamming Discord.
    if not seen:
        for job, _, _ in matches:
            seen.add(job_id(job))

        save_seen(seen)

        print(
            f"Initialized with {len(seen)} existing "
            "early-talent opportunities."
        )
        print("No Discord notifications sent.")
        return

    new_count = 0

    for job, confidence, keyword in matches:
        identifier = job_id(job)

        if identifier in seen:
            continue

        print(
            f"NEW: [{confidence}] "
            f"{job['company']} - {job['role']}"
        )

        send_discord(
            job,
            confidence,
            keyword,
        )

        seen.add(identifier)
        new_count += 1

    save_seen(seen)

    print(f"Found {new_count} new opportunities.")
    print("Done!")


if __name__ == "__main__":
    main()