import requests
from bs4 import BeautifulSoup
import csv
from time import sleep


# List of company domains
def read_csv_to_list(file_path):
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        return [row for row in reader]  # Assuming each row has one column


# Read company domains from CSV file
company_domains = read_csv_to_list("career_pages2.csv")
# print(company_domains)
# Common career page paths
career_paths = [
    "/careers",
    "/careers/",
    "/jobs",
    "/jobs/",
    "/about/careers",
    "/company/careers",
    "/en/careers",
    "/employment",
    "/work-with-us",
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def find_careers_page(domain):
    for path in career_paths:
        url = domain.rstrip("/") + path
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"[FOUND] Careers page for {domain}: {url}")
                return url
        except requests.RequestException as e:
            print(f"[ERROR] {url}: {e}")

    # Fallback: Try to scrape the homepage for career-related links
    try:
        response = requests.get(domain, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"].lower()
                if "career" in href or "job" in href or "work" in href:
                    if href.startswith("http"):
                        print(f"[SCRAPED] Possible careers page for {domain}: {href}")
                        return href
                    else:
                        full_url = domain.rstrip("/") + "/" + href.lstrip("/")
                        print(
                            f"[SCRAPED] Possible careers page for {domain}: {full_url}"
                        )
                        return full_url
    except requests.RequestException as e:
        print(f"[ERROR] Failed to scrape {domain}: {e}")

    print(f"[NOT FOUND] No careers page found for {domain}")
    return "Not Found"


# Find career pages
# career_pages = []
# for domain in company_domains:
#     careers_url = find_careers_page(domain)
#     career_pages.append({"Company Domain": domain, "Careers Page URL": careers_url})
#     sleep(2)

# # Save results to CSV
# csv_filename = "career_pages.csv"
# with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
#     fieldnames = ["Company Domain", "Careers Page URL"]
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#     writer.writeheader()
#     writer.writerows(career_pages)

# print(f"\n✅ Results saved to {csv_filename}")


import requests
from bs4 import BeautifulSoup
import sys
import base64
import os
from dotenv import load_dotenv
from google.genai import types
from google import genai


load_dotenv()

linkRanker = """You are a specialized URL evaluator with expertise in identifying job listing websites. You'll be given a list of URLs, and your task is to analyze them and identify the top 5 most likely to contain job listings.

When analyzing each URL, consider these characteristics:

1. HIGHEST PRIORITY - Direct job application or job search paths:
   - URLs containing "/jobs", "/careers", "/employment", "job-search", or similar job-specific paths
   - Job application portals (like "jobs.company.com")
   - URLs with paths containing "search" combined with job-related contexts

2. HIGH PRIORITY - Career information pages:
   - URLs containing "work-at-[company]", "life-at-[company]"
   - Career index pages ("/careers/index.html")
   - Department-specific career pages ("/careers/retail", "/careers/software")
   - Paths containing "recruitment", "hiring", or "positions"

3. MEDIUM PRIORITY - URL fragments suggesting job-related content:
   - Relative paths leading to career sections
   - URLs containing "profile", "apply", or "application" in a context suggesting employment
   - Specialized department hiring pages (engineering, technical, support)

Ignore:
   - Shopping cart pages ("/bag", "/shop", "/store")
   - Support or customer service pages (unless specifically for job applications)
   - Media files (CSS, video) unless they're directly job-related content
   - General product, service, or company information pages

For each URL, assign a confidence score (0-100) based on how likely it contains job listings, with brief reasoning.

Return only the top 5 URLs with highest scores, ranked from highest to lowest probability, formatted as:
1. [URL] - [Score]/100: [Brief explanation]
2. [URL] - [Score]/100: [Brief explanation]
...

If multiple URLs have equal scores, prioritize:
- Complete URLs over relative paths
- Job search/application pages over informational career pages
- Department-specific career pages over general career pages
- URLs with cleaner, simpler structures

Include no other text in your response beyond this ranked list."""


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


def extract_hrefs(url):
    """
    Fetch HTML from a URL and extract all href attributes from links.

    Args:
        url (str): The URL to fetch and parse

    Returns:
        list: A list of all href values found in the page
    """
    try:
        # Send HTTP request to the URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)

        # Check if the request was successful
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all elements with href attributes
        links = []
        for link in soup.find_all(href=True):
            links.append(link["href"])

        return links

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return []


def append_to_csv(file_path, new_data):
    """
    Append a row of data to an existing CSV file.

    Args:
        file_path (str): Path to the CSV file
        new_data (list): List of values to append as a new row
    """
    with open(file_path, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(new_data)


def main():
    # Check if URL was provided as command line argument
    for company_domain in company_domains:
        print(f"Processing {company_domain[0]}...")
        if company_domain[1] != "Not Found":
            hrefs = extract_hrefs(company_domain[1])
            links = []
            if hrefs:
                print(f"Found {len(hrefs)} links on {company_domain}:")
                for i, href in enumerate(hrefs, 1):
                    links.append(href)
                    # print(f"{i}. {href}")
            else:
                print(f"No links found on {company_domain}")
            response = generate(linkRanker + "\n".join(links))
            print(response)
            append_to_csv("job_links.csv", [company_domain, response])
            sleep(10)
        else:
            append_to_csv("job_links.csv", [company_domain[0], "Not Found"])


if __name__ == "__main__":
    main()
