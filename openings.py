import requests
from bs4 import BeautifulSoup
import re


def get_highest_scored_link(links_with_scores):
    # Parse the string to extract links and scores
    highest_score = 0
    highest_scored_link = ""

    # Regular expression to match links with scores
    pattern = r"(\d+)\. (https?://[^\s]+|/[^\s]+) - (\d+)/100:"

    for line in links_with_scores.strip().split("\n"):
        match = re.search(pattern, line)
        if match:
            link = match.group(2)
            score = int(match.group(3))

            if score > highest_score:
                highest_score = score
                highest_scored_link = link

    return highest_scored_link


def visit_link(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print(f"Successfully accessed {url}")
            print(f"Status code: {response.status_code}")

            # Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract and print the title
            title = soup.title.string if soup.title else "No title found"
            print(f"Page title: {title}")

            # Print first 100 characters of content
            content_text = soup.get_text().strip()
            print(f"Content preview: {content_text[:100]}...")

        else:
            print(f"Failed to access {url}")
            print(f"Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Sample data from input
    links_with_scores = """1. https://jobs.apple.com/en-us/search - 100/100: Direct job search portal on Apple's jobs domain, highest priority.
2. https://jobs.apple.com/app/en-us/profile/info - 95/100: Direct link to profile information page in Apple's job application portal, suggesting account management for job applications.
3. https://www.apple.com/careers/us/ - 90/100:  Direct path to US careers page, very likely to contain job listings.
4. /careers/us/index.html - 80/100: Relative path pointing to US careers index page, suggests job listings.
5. /careers/us/retail.html - 70/100: Relative path pointing to retail careers page, suggests a specific department's hiring information."""

    highest_link = get_highest_scored_link(links_with_scores)
    print(f"Highest scored link: {highest_link}")

    # Visit the highest scored link
    if highest_link:
        visit_link(highest_link)
    else:
        print("No valid link found.")
