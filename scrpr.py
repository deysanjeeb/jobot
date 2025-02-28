import requests
import json
import pandas as pd
from time import sleep
from duckduckgo_search import DDGS


def duckduckgo_search(query):
    """
    Perform a search using the DuckDuckGo Instant Answer API and return the first URL.

    :param query: The search query string.
    :return: The first URL from the search results, or None if no results are found.
    """
    # DuckDuckGo API endpoint
    url = "https://api.duckduckgo.com/"

    # Parameters for the API request
    params = {
        "q": query,  # Search query
        "format": "json",  # Response format
        "no_html": 1,  # Exclude HTML from results
        "skip_disambig": 1,  # Skip disambiguation pages
    }

    # Send GET request to the API
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        results = response.json()
        # print(json.dumps(results, indent=4))
        # Extract the first URL from the results
        if results.get("Results"):
            # print(results["Results"])  # Return the first URL
            return results["Results"][0]["FirstURL"]
        elif results.get("RelatedTopics"):
            # Check the first related topic for a URL
            for topic in results["RelatedTopics"]:
                if topic.get("FirstURL"):
                    return topic["FirstURL"]
        else:
            return None  # No URL found
    else:
        print(f"Error: Unable to fetch results (Status Code: {response.status_code})")
        return None


def firstLink(query):
    results = DDGS().text(query, max_results=2)

    return [results[0]["href"], results[1]["href"]]


if __name__ == "__main__":
    df = pd.read_csv("sp500_companies.csv")
    # Get user input for the search query

    df["URL"] = ""

    for index, row in df.iterrows():
        company = row["Longname"]
        # Perform the search and get the first URL
        first_url = firstLink(company)

        # Update the DataFrame with the first URL
        df.at[index, "URL"] = first_url

        # Display the result
        if first_url:
            print(f"First URL for '{company}': {first_url}")
        else:
            print(f"No results found for '{company}'.")
        sleep(2)

    # Save the updated DataFrame to a new CSV file
    df.to_csv("updated_companies.csv", index=False)

    print(df)
