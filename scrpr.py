import requests
from bs4 import BeautifulSoup
import csv
from time import sleep


# List of company domains
def read_csv_to_list(file_path):
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        return [row[1] for row in reader]  # Assuming each row has one column


# Read company domains from CSV file
company_domains = read_csv_to_list("sp500_links.csv")
print(company_domains)
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


def main():
    # Check if URL was provided as command line argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <url>")
        print("Example: python script.py https://example.com")
        sys.exit(1)

    url = sys.argv[1]
    hrefs = extract_hrefs(url)
    links = []
    if hrefs:
        print(f"Found {len(hrefs)} links on {url}:")
        for i, href in enumerate(hrefs, 1):
            links.append(href)
            print(f"{i}. {href}")
    else:
        print(f"No links found on {url}")


if __name__ == "__main__":
    main()
