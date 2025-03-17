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
