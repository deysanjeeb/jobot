import asyncio
import csv
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, SecretStr
from PyPDF2 import PdfReader

from browser_use import ActionResult, Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
import requests

# Validate required environment variables
load_dotenv()

logger = logging.getLogger(__name__)
# full screen mode
controller = Controller()

# NOTE: This is the path to your cv file
CV = Path.cwd() / "Back End.pdf"

# if not CV.exists():
# 	raise FileNotFoundError(f'You need to set the path to your cv file in the CV variable. CV file not found at {CV}')


def llm_friendly_content(url: str):
    """
    This function is used to format the content in a way that is friendly for LLMs.
    It can be used to extract specific information from the content.
    """

    # Here you can implement your logic to format the content
    # For example, you can use regex to extract specific information

    """
    Sends a GET request to the specified URL and returns the text content of the response.
    """
    try:
        jina = "https://r.jina.ai/" + url
        response = requests.get(jina)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        logger.info(f"Fetched text from URL {response.text}")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch text from URL {url}: {e}")
        return ""


class Job(BaseModel):
    title: str
    link: str
    company: str
    fit_score: float
    location: Optional[str] = None
    salary: Optional[str] = None


@controller.action(
    "Save jobs to file - with a score how well it fits to my profile", param_model=Job
)
def save_jobs(job: Job):
    with open("jobs.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([job.title, job.company, job.link, job.salary, job.location])

    return "Saved job to file"


class Position(BaseModel):
    url: str


@controller.action("Read jobs from file")
def read_jobs():
    with open("jobs.csv", "r") as f:
        return f.read()


@controller.action("Read my cv for context to fill forms")
def read_cv():
    pdf = PdfReader(CV)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""
    logger.info(f"Read cv with {len(text)} characters")
    return ActionResult(extracted_content=text, include_in_memory=True)


@controller.action(
    "Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element",
)
async def upload_cv(index: int, browser: BrowserContext):
    path = str(CV.absolute())
    dom_el = await browser.get_dom_element_by_index(index)

    if dom_el is None:
        return ActionResult(error=f"No element found at index {index}")

    file_upload_dom_el = dom_el.get_file_upload_element()

    if file_upload_dom_el is None:
        logger.info(f"No file upload element found at index {index}")
        return ActionResult(error=f"No file upload element found at index {index}")

    file_upload_el = await browser.get_locate_element(file_upload_dom_el)

    if file_upload_el is None:
        logger.info(f"No file upload element found at index {index}")
        return ActionResult(error=f"No file upload element found at index {index}")

    try:
        await file_upload_el.set_input_files(path)
        msg = f'Successfully uploaded file "{path}" to index {index}'
        logger.info(msg)
        return ActionResult(extracted_content=msg)
    except Exception as e:
        logger.debug(f"Error in set_input_files: {str(e)}")
        return ActionResult(error=f"Failed to upload file to index {index}")


@controller.action("Save URL", param_model=Position)
def save_url(params: Position):
    logger.info(params.url)
    parameters.append_row([params.url])
    llm_friendly_content(params.url)


browser = Browser(
    config=BrowserConfig(
        disable_security=True,
        # chrome_instance_path="/usr/bin/google-chrome"
        # cdp_url="http://localhost:9222",
    )
)

initial_actions = [
    {"open_tab": {"url": "https://www.jobright.ai/jobs/recommended"}},
]


async def main():
    # ground_task = (
    # 	'You are a professional job finder. '
    # 	'1. Read my cv with read_cv'
    # 	'2. Read the saved jobs file '
    # 	'3. start applying to the first link of Amazon '
    # 	'You can navigate through pages e.g. by scrolling '
    # 	'Make sure to be on the english version of the page'
    # )
    ground_task = (
        "You are a professional job finder. "
        "1. Read my cv with read_cv "
        "find ml internships in and save them to a file "
        "search at company:"
    )
    tasks = [
        """Click on the first Apply now button only once""",
        """wait 5 seconds""",
        """Click on apply now""",
        """wait 5 seconds""",
        """Save URL of the current page""",
    ]
    api_key = os.getenv("GEMINI_API_KEY")

    # Initialize the model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", api_key=SecretStr(os.getenv("GEMINI_API_KEY"))
    )

    # agents = []
    # for task in tasks:
    #     agent = Agent(task=task, llm=llm, controller=controller, browser=browser)
    #     agents.append(agent)

    # await asyncio.gather(*[agent.run() for agent in agents])

    agent = Agent(
        task=tasks,
        llm=llm,
        controller=controller,
        browser=browser,
        initial_actions=initial_actions,
    )
    await agent.run()


if __name__ == "__main__":
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "secrets/credentials.json", scope
    )

    # Authenticate with Google
    client = gspread.authorize(creds)
    jobslist = client.open("job applications")
    parameters = jobslist.get_worksheet(0)

    # Add a new row to the sheet

    asyncio.run(main())
