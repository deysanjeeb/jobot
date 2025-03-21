openPositions = """You are tasked with identifying and listing job position links from a given set of URL and text pairs. Follow these instructions carefully:

1. You will be provided with a list of URL and text pairs in the following format:
<url_text_pairs>
{URL_TEXT_PAIRS}
</url_text_pairs>

2. Analyze each URL and text pair to identify those that represent job positions. Job position links typically have the following characteristics:
   - The URL contains "/details/" followed by a job ID or title
   - The text describes a specific job title or role

3. Create a list of all the URLs that correspond to job positions. Do not include any other types of links (e.g., sign-in pages, general career pages, etc.).

4. Present your list of job position links in the following format:
<job_position_links>
[List your identified job position links here, one per line]
</job_position_links>

5. If you find no job position links, output:
<job_position_links>
No job position links found.
</job_position_links>

Provide only the list of job position links without any additional commentary or explanation."""

openPositions2 = """You are an AI assistant tasked with identifying job position links from a set of URL and text pairs. Your goal is to create a list of links that specifically point to individual job postings, excluding any other types of pages such as general career pages, sign-in pages, or non-job-related content.

Here is the set of URL and text pairs you need to analyze:

<url_text_pairs>
{URL_TEXT_PAIRS}
</url_text_pairs>

Please follow these steps to complete the task:

1. Analyze each URL and text pair in the given set.

2. For each pair, use the following criteria to determine if it's a job position link:
   - The URL should contain keywords like "jobs", "careers", "positions", or "openings"
   - The URL should include a specific job identifier or title
   - The accompanying text should describe a job title or role
   - Exclude links to general career pages, sign-in pages, or non-job-related content

3. If you determine a link is for a job position, add it to your list of job position links.

4. After analyzing all pairs, present your final list of job position links in the following format:

<job_position_links>
[List your identified job position links here, one per line]
</job_position_links>

If you find no job position links, output:

<job_position_links>
No job position links found.
</job_position_links>

Remember to provide only the list of job position links without any additional commentary or explanation."""

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

nextCheck = """You are an AI system designed to analyze URLs and identify links to the "Next" page in pagination systems. Your task is to examine a list of URLs and determine the most likely candidate for the "Next" page link.

Here is the list of URLs you need to analyze:

<url_list>
{URL_LIST}
</url_list>

Instructions:
1. Examine the provided URL list.
2. Analyze each URL for patterns or keywords that might indicate it leads to a "Next" page.
3. Consider the following common indicators:
   - The word "next" or "page" in the URL
   - Increasing numerical values, especially at the end of the URL
   - Query parameters like "page=2" or "offset=10"
4. Select the single most likely URL that represents the "Next" page link.
5. If no URL seems to indicate a "Next" page, state that none were found.

Before providing your final result, wrap your thought process in <url_evaluation> tags. In this evaluation:
- List each URL and categorize it as "Potential Next Link", "Unlikely Next Link", or "Inconclusive".
- For each "Potential Next Link" and "Inconclusive" URL, list the indicators that support it being a Next link and any factors that make it less likely.
- Rank the potential Next links in order of likelihood.
- Explain your final decision, including why you chose the top-ranked URL over others (if applicable).

Your final output should be a single URL (or a statement that no "Next" page link was found) within <result> tags.

Example output structure:

<url_evaluation>
[Your detailed analysis of the URLs, explaining your reasoning for each potential "Next" page link]
</url_evaluation>

<result>
[Either a single URL representing the most likely "Next" page link, or "No Next page link found."]
</result>

Remember:
- Only provide one link in your final result.
- Do not include any additional information or explanation in the <result> tags.
- If the URL list is empty or contains invalid URLs, state this in your analysis and result.
- Context is important. A URL ending in a number doesn't always indicate a "Next" page, so consider the overall structure and pattern of the URLs in your analysis.

Please proceed with your evaluation and provide the result."""
