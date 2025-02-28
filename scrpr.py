import requests
import json


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
    # response = requests.get(
    #     "https://api.duckduckgo.com/?q=AppleInc&format=json&pretty=1&no_html=1&skip_disambig=1"
    # )
    # Check if the request was successful
    if response.status_code == 200:
        results = response.json()
        print(json.dumps(results, indent=4))
        # Extract the first URL from the results
        if results.get("Results"):
            print(results["Results"])  # Return the first URL
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


if __name__ == "__main__":
    # Get user input for the search query
    query = input("Enter your search query: ")

    # Perform the search and get the first URL
    first_url = duckduckgo_search(query)

    # Display the result
    if first_url:
        print(f"First URL for '{query}': {first_url}")
    else:
        print(f"No results found for '{query}'.")
