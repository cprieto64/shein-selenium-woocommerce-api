from faker import Faker
from config import list_of_domains

fake = Faker()
fakename = Faker('es_CO')

def fakemail():
    """Generates a fake email address using a random domain from list_of_domains."""
    domain = fake.random_element(elements=list_of_domains)
    # Ensure the domain doesn't have a trailing slash for email generation
    if domain.endswith('/'):
        domain = domain[:-1]
    # Remove "https://" or "http://" from the domain for the email
    if domain.startswith("https://"):
        domain = domain[8:]
    elif domain.startswith("http://"):
        domain = domain[7:]
    return f"{fake.user_name()}@{domain}"
