from dotenv import load_dotenv
import requests
import os

# load environment variables
load_dotenv()

# get variables values from environment
BASE_API_URL = os.getenv('SOURCE_SUPERSET_API_URL')
USERNAME = os.getenv('SUPERSET_USERNAME')
PASSWORD = os.getenv('SUPERSET_PASSWORD')
EXPORT_FOLDER = os.getenv('EXPORT_FOLDER')


def get_authentication_token():
    """Function for requesting authentication token to loging in Superset."""

    response = requests.post(f"{BASE_API_URL}/security/login", json={
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db"
    })
    response.raise_for_status()
    return response.json()["access_token"]
