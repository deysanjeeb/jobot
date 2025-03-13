import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import csv
import prompts
from dotenv import load_dotenv
from google.genai import types
from google import genai
import os
from pprint import pprint
import xml.etree.ElementTree as ET

load_dotenv()


def extract_domain(url):
    """
    Extract the domain from a URL.

    Args:
        url (str): The URL string

    Returns:
        str: The extracted domain
    """
    pattern = r"https?://([^/]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def filter_jobs_apple_links(links_list, highest_link):
    """
    Filter a list of links to keep only those from the jobs.apple.com subdomain.

    Args:
        links_list (list): A list of dictionaries containing URLs and their text

    Returns:
        list: A list of dictionaries containing filtered links with their index, URL, and text
    """
    jobs_links = []
    print(highest_link)

    for i, link in enumerate(links_list):
        parsed_url = urlparse(link["url"])
        if parsed_url.netloc == extract_domain(highest_link):
            jobs_links.append(
                {"index": i + 1, "url": link["url"], "text": link["text"]}
            )

    return jobs_links


def get_highest_scored_link(links_with_scores):
    # Parse the string to extract links and scores
    highest_score = 0
    highest_scored_link = ""

    # Regular expression to match links with scores
    pattern = r"(\d+)\. +(https?://[^\s]+|/[^\s]+) - (\d+)/100:"

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
            # for i, link in enumerate(links, 1):
            #     print(f"{i}. {link['url']} - \"{link['text']}\"")

            return links

        else:
            print(f"Failed to access {url}")
            print(f"Status code: {response.status_code}")
            return []

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def generate(prompt):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="text/plain",
    )

    # for chunk in client.models.generate_content_stream(
    #     model=model,
    #     contents=contents,
    #     config=generate_content_config,
    # ):
    #     print(chunk.text, end="")
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=contents
    )
    return response.text


if __name__ == "__main__":
    csv_path = "job_links.csv"
    companies = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            companies.append({"url": row["Domain"], "text": row["Links"]})
    # Sample data from input
    links_with_scores = """1. https://jobs.apple.com/en-us/search - 100/100: Direct job search portal on Apple's jobs domain, highest priority.
2. https://jobs.apple.com/app/en-us/profile/info - 95/100: Direct link to profile information page in Apple's job application portal, suggesting account management for job applications.
3. https://www.apple.com/careers/us/ - 90/100:  Direct path to US careers page, very likely to contain job listings.
4. /careers/us/index.html - 80/100: Relative path pointing to US careers index page, suggests job listings.
5. /careers/us/retail.html - 70/100: Relative path pointing to retail careers page, suggests a specific department's hiring information."""
    for company in companies:
        print(f"Analyzing links for {company['url']}...")
        print(f"Links: {company['text']}")
        highest_link = get_highest_scored_link(company["text"])

        print(f"Highest scored link: {highest_link}")
        all_links = extract_links(highest_link)
        # Save links to a file
        with open("extracted_links.txt", "w", encoding="utf-8") as f:
            f.write(f"Links extracted from {company['url']}:\n\n")
            for i, link in enumerate(all_links, 1):
                f.write(f"{i}. {link['url']} - \"{link['text']}\"\n")
        print(all_links)
        print(f"\nAll links have been saved to 'extracted_links.txt'")
        # Filter the links
        filtered_links = filter_jobs_apple_links(all_links, highest_link)

        # Print the filtered links
        # print(filtered_links)
        formatted_prompt = prompts.openPositions.format(URL_TEXT_PAIRS=filtered_links)
        response = generate(formatted_prompt)
        filteredLines = [
            line for line in response.split("\n") if not line.strip().startswith("```")
        ]
        cleanResponse = "\n".join(filteredLines)
        root = ET.ElementTree(ET.fromstring(cleanResponse)).getroot()

        # Extract job links (handling text within the root element)
        job_links = [line.strip() for line in root.text.strip().split("\n")]
        print(len(job_links))
        pprint(job_links)

        # Optionally, save to a new file
        with open("filtered_jobs_links.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Text"])
            for link in filtered_links:
                writer.writerow([link["url"], link["text"]])

        print(f"\nFiltered links saved to 'filtered_jobs_links.csv'")
