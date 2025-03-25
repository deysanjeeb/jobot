import time
import requests
import json
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
import sqlite3  # Added SQLite import
import ast
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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


def extract_workday_job_links(url):
    """
    Extracts job listing links from a Workday careers page.

    Args:
        url (str): The Workday careers or job search URL

    Returns:
        list: List of job posting URLs
    """
    job_links = []

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None

    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # Wait for job listings to load (common Workday selectors)
        wait = WebDriverWait(driver, 15)

        # Look for job cards/links using various common Workday selectors
        selectors = [
            "a[data-automation-id='jobTitle']",  # Most common
            ".jobTitle a",
            ".job-link",
            "[data-automation-id='jobSearchResultsList'] a",
            ".WB33 a",  # Some Workday instances use this class
            ".job-card a",
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Wait for at least one element to be present
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

                # Get all matching elements
                job_elements = driver.find_elements(By.CSS_SELECTOR, selector)

                if job_elements:
                    # Extract links
                    for element in job_elements:
                        href = element.get_attribute("href")
                        if (
                            href and "job/" in href
                        ):  # Most Workday job links contain "job/"
                            job_links.append(href)

                    # If we found links, no need to try other selectors
                    if job_links:
                        break
            except:
                # If this selector didn't work, try the next one
                continue

        # If the above selectors didn't work, try a more generic approach
        if not job_links:
            # Look for any links that might be job postings
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                href = link.get_attribute("href")
                # Filter for likely job posting links
                if href and re.search(
                    r"(job|requisition|position|career|opening|JobReq)",
                    href,
                    re.IGNORECASE,
                ):
                    job_links.append(href)

        # Remove duplicates while preserving order
        job_links = list(dict.fromkeys(job_links))

    except Exception as e:
        print(f"Error extracting job links: {str(e)}")
        return []

    finally:
        # Always close the driver
        if driver:
            driver.quit()

    return job_links


def filter_subdomain_links(links_list, highest_link):
    """
    Filter a list of links to keep only those from the subdomain.

    Args:
        links_list (list): A list of dictionaries containing URLs and their text

    Returns:
        list: A list of dictionaries containing filtered links with their index, URL, and text
    """
    jobs_links = []
    # print(highest_link)

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

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=contents
    )
    return response.text


def setup_database():
    """
    Set up SQLite database with a table for job links
    """
    conn = sqlite3.connect("job_links.db")
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS job_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        link TEXT NOT NULL,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    conn.commit()
    conn.close()
    print("Database setup complete")


def save_job_links_to_db(job_links, company_name):
    """
    Save job links to SQLite database

    Args:
        job_links (list): List of job links
        company_url (str): The company URL/domain
    """
    if not job_links:
        print(f"No job links to save for {company_name}")
        return

    conn = sqlite3.connect("job_links.db")
    cursor = conn.cursor()

    # Insert links
    for link in job_links:
        cursor.execute(
            "INSERT INTO job_links (company, link) VALUES (?, ?)", (company_name, link)
        )

    conn.commit()
    print(f"Saved {len(job_links)} job links for {company_name} to database")
    conn.close()


if __name__ == "__main__":
    # Set up the database first
    setup_database()

    csv_path = "job_links.csv"
    companies = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            converted_list = ast.literal_eval(row["Domain"])
            companies.append({"url": converted_list, "text": row["Links"]})

    for company in companies:
        highest_link = ""
        print(f"Analyzing links for {company['url'][0]}...")
        # print(f"Links: {company['text']}")
        highest_link = get_highest_scored_link(company["text"])

        print(f"Highest scored link: {highest_link}")
        if "workday" in highest_link:
            continue
            job_info = extract_workday_job_links(highest_link)
            print("\nExtracted job information:")
            pprint(job_info)
        elif highest_link:
            all_links = extract_links(highest_link)
        elif "example" in highest_link:
            continue
        else:
            print("No valid links found.")
            continue

        # Save links to a file (keeping this for debugging)
        # with open("extracted_links.txt", "a", encoding="utf-8") as f:
        #     f.write(f"Links extracted from {company['url']}:\n\n")
        #     for i, link in enumerate(all_links, 1):
        #         f.write(f"{i}. {link['url']} - \"{link['text']}\"\n")

        # print(f"\nAll links have been saved to 'extracted_links.txt'")

        # Filter the links
        filtered_links = filter_subdomain_links(all_links, highest_link)

        formatted_prompt = prompts.openPositions2.format(URL_TEXT_PAIRS=filtered_links)
        response = generate(formatted_prompt)

        filteredLines = [
            line for line in response.split("\n") if not line.strip().startswith("```")
        ]
        cleanResponse = "\n".join(filteredLines)
        try:
            root = ET.ElementTree(ET.fromstring(cleanResponse)).getroot()

            # Extract job links (handling text within the root element)
            job_links = [line.strip() for line in root.text.strip().split("\n")]

            # Save job links to SQLite database instead of CSV
            save_job_links_to_db(job_links, company["url"][0])

            formatted_prompt = prompts.nextCheck.format(URL_TEXT_PAIRS=filtered_links)
            nextLink = generate(formatted_prompt)
            print("next link result: ", nextLink)

            print(f"\nFiltered links saved to database")
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {response}")
            continue
        break
