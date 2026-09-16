# early-talent-discord-bot
# Early Talent Discord Bot

A custom Discord bot built to automatically track, scrape, and share real-time early talent opportunities—including internships, new grad roles, and rotational programs—so community members never miss an application deadline.

Created and maintained by **Ryan Tsui** (Director of Professional Development).

---

## What It Does

* **Automated Opportunity Scraping:** Scans target job boards, GitHub repos, and company career portals on a scheduled loop.
* **Real-Time Discord Alerts:** Sends clean, embedded notifications straight to designated Discord channels whenever new openings are detected.
* **Smart Deduplication:** Keeps track of previously posted listings in a local `seen_jobs.json` file to avoid repeating alerts.
* **Role & Tag Filtering:** Supports targeted keyword filtering across software engineering, product management, data science, and hardware paths.

---

## Tech Stack

* **Language:** Python 3.8+
* **Scraping & Requests:** BeautifulSoup4, Requests, Selenium
* **Discord API:** `discord.py` / Webhooks
* **State Management:** JSON file tracking (`seen_jobs.json`)

---

## Quick Setup

### 1. Prerequisites
Make sure you have **Python 3.8+** installed on your system.

### 2. Installation
Clone the repository and install the required dependencies:

```bash
git clone [https://github.com/rtsui335/early-talent-discord-bot.git](https://github.com/rtsui335/early-talent-discord-bot.git)
cd early-talent-discord-bot
pip install -r requirements.txt
