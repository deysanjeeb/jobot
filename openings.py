import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
from google.genai import types
from google import genai


load_dotenv()


def filter_jobs_apple_links(links_list):
    """
    Filter a list of links to keep only those from the jobs.apple.com subdomain.

    Args:
        links_list (list or str): Either a list of URLs or a string with numbered URLs (one per line)

    Returns:
        list: A list of dictionaries containing filtered links with their index, URL, and text
    """
    # Process input if it's a string
    if isinstance(links_list, str):
        # Regular expression to extract links from numbered list
        pattern = r'(\d+)\. (https?://[^\s]+) - "(.*?)"'
        links = []

        for line in links_list.strip().split("\n"):
            match = re.match(pattern, line)
            if match:
                index = int(match.group(1))
                url = match.group(2)
                text = match.group(3)
                links.append({"index": index, "url": url, "text": text})
    else:
        # Assume links_list is already a list of URLs
        links = [
            {"index": i + 1, "url": url, "text": ""} for i, url in enumerate(links_list)
        ]

    # Filter links to include only jobs.apple.com
    jobs_links = []

    for link in links:
        parsed_url = urlparse(link["url"])
        if parsed_url.netloc == "jobs.apple.com":
            jobs_links.append(link)

    return jobs_links


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


def extract_links(url):
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

            # Extract all links
            links = []
            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]

                # Skip javascript and anchor links
                if href.startswith("javascript:") or href.startswith("#"):
                    continue

                # Convert relative URLs to absolute URLs
                if not href.startswith(("http://", "https://")):
                    href = urljoin(base_url, href)

                link_text = a_tag.text.strip()
                if not link_text:
                    link_text = "No text"

                links.append(
                    {
                        "url": href,
                        "text": link_text[:50] + ("..." if len(link_text) > 50 else ""),
                    }
                )

            print(f"\nFound {len(links)} links on the page:\n")

            # Print all links with their text
            for i, link in enumerate(links, 1):
                print(f"{i}. {link['url']} - \"{link['text']}\"")

            return links

        else:
            print(f"Failed to access {url}")
            print(f"Status code: {response.status_code}")
            return []

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    # Sample data from input
    links_with_scores = """1. https://jobs.apple.com/en-us/search - 100/100: Direct job search portal on Apple's jobs domain, highest priority.
2. https://jobs.apple.com/app/en-us/profile/info - 95/100: Direct link to profile information page in Apple's job application portal, suggesting account management for job applications.
3. https://www.apple.com/careers/us/ - 90/100:  Direct path to US careers page, very likely to contain job listings.
4. /careers/us/index.html - 80/100: Relative path pointing to US careers index page, suggests job listings.
5. /careers/us/retail.html - 70/100: Relative path pointing to retail careers page, suggests a specific department's hiring information."""

    highest_link = get_highest_scored_link(links_with_scores)
    print(f"Highest scored link: {highest_link}")

    # Visit the highest scored link and extract all links
    if highest_link:
        all_links = extract_links(highest_link)

        # Save links to a file
        with open("extracted_links.txt", "w", encoding="utf-8") as f:
            f.write(f"Links extracted from {highest_link}:\n\n")
            for i, link in enumerate(all_links, 1):
                f.write(f"{i}. {link['url']} - \"{link['text']}\"\n")

        print(f"\nAll links have been saved to 'extracted_links.txt'")
    else:
        print("No valid link found.")

    with open("extracted_links.txt", "r", encoding="utf-8") as f:
        links_text = f.read()

    # Filter the links
    filtered_links = filter_jobs_apple_links(links_text)

    # Print the filtered links
    print(filtered_links)

    # Optionally, save to a new file
    with open("filtered_jobs_links.txt", "w", encoding="utf-8") as f:
        f.write("Links from jobs.apple.com:\n\n")
        for link in filtered_links:
            f.write(f"{link['index']}. {link['url']} - \"{link['text']}\"\n")

    print(f"\nFiltered links saved to 'filtered_jobs_links.txt'")
