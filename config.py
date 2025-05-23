import os
from dotenv import load_dotenv

load_dotenv()

list_of_domains = (
    "https://www.example.com",
    "https://www.anotherdomain.net",
    # Add more domains as needed
)

WC_CONSUMER_KEY = os.getenv("CONSUMER_KEY")
WC_CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
