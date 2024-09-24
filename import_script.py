from helpers import BASE_API_URL, EXPORT_FOLDER
from helpers import get_authentication_token
from urllib.parse import quote
import requests
import json
import glob
import uuid
import os
import re


def simplify_chart_data(data):
    """Function for simplifying chart data for request."""

    return {
        "cache_timeout": data.get("cache_timeout"),
        "certification_details": data.get("certification_details"),
        "certified_by": data.get("certified_by"),
        "dashboards": [dashboard["id"] for dashboard in data.get("dashboards", [])],
        "datasource_id": data.get("datasource_id"),
        "datasource_name": data.get("datasource_name_text"),
        "datasource_type": data.get("datasource_type"),
        "description": data.get("description"),
        "external_url": data.get("external_url"),
        "is_managed_externally": data.get("is_managed_externally"),
        "owners": [owner["id"] for owner in data.get("owners", [])],
        "params": data.get("params"),
        "query_context": data.get("query_context"),
        "query_context_generation": data.get("query_context_generation"),
        "slice_name": data.get("slice_name"),
        "viz_type": data.get("viz_type")
    }


def is_slug_unique(slug, token):
    """Function for verifying the unicity of slug parameter."""

    headers = {"Authorization": f"Bearer {token}"}
    query = {
        "filters": [
            {
                "col": "slug",
                "opr": "eq",
                "value": slug
            }
        ]
    }

    response = requests.get(f"{BASE_API_URL}/dashboard/?q={quote(json.dumps(query))}", headers=headers)
    response.raise_for_status()
    return len(response.json()["result"]) == 0


def simplify_dashboard_data(data, token):
    """Function for simplifying dashboard data for request."""

    slug = data.get("slug") if data.get("slug") is not None else f"default-slug-{uuid.uuid4()}"

    # verify is slug parameter is unique, otherwise generate unique slug
    while not is_slug_unique(slug, token):
        slug = f"default-slug-{uuid.uuid4()}"

    return {
        "certification_details": data.get("certification_details") if data.get(
            "certification_details") is not None else "No certification details provided",
        "certified_by": data.get("certified_by") if data.get("certified_by") is not None else "Not certified",
        "css": data.get("css") if data.get("css") is not None else "/* Default CSS */",
        "dashboard_title": data.get("dashboard_title") if data.get(
            "dashboard_title") is not None else "Untitled Dashboard",
        "external_url": data.get("external_url") if data.get("external_url") is not None else "http://example.com",
        "is_managed_externally": data.get("is_managed_externally") if data.get(
            "is_managed_externally") is not None else False,
        "json_metadata": data.get("json_metadata") if data.get("json_metadata") is not None else "{}",
        "owners": [owner["id"] for owner in data.get("owners", [])],
        "position_json": data.get("position_json") if data.get("position_json") is not None else "{}",
        "published": data.get("published") if data.get("published") is not None else False,
        "roles": [role["id"] for role in data.get("roles", [])],
        "slug": slug
    }


def simplify_dataset_data(data):
    """Function for simplifying dataset data for request."""

    return {
        "database": data["database"]["id"],
        "external_url": data.get("external_url", ""),
        "is_managed_externally": data.get("is_managed_externally", False),
        "owners": [owner["id"] for owner in data.get("owners", [])],
        "schema": data.get("schema", ""),
        "sql": data.get("sql", ""),
        "table_name": data.get("table_name", "")
    }


def dataset_exists(dataset_name, token):
    """Function for verifying the presence of a dataset."""

    headers = {"Authorization": f"Bearer {token}"}
    query = {
        "filters": [
            {
                "col": "table_name",
                "opr": "eq",
                "value": dataset_name
            }
        ]
    }

    response = requests.get(f"{BASE_API_URL}/dataset/?q={quote(json.dumps(query))}", headers=headers)
    response.raise_for_status()
    return len(response.json()["result"]) > 0


def get_csrf_token_and_cookies(token):
    """Function for retrieving security token and cookies."""

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_API_URL}/security/csrf_token/", headers=headers)
    response.raise_for_status()

    csrf_token = response.json()["result"]
    cookies = response.cookies

    return csrf_token, cookies


def import_entity(entity, file_path):
    """Function for importing entity in Superset."""

    # get authentication token
    token = get_authentication_token()

    # get security token
    csrf_token, cookies = get_csrf_token_and_cookies(token)

    # make header request
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
    }

    # load data from json file
    with open(file_path, "r") as f:
        data = json.load(f)

    # simplify data for each entity type
    if entity == "chart":
        simplified_data = simplify_chart_data(data)
    elif entity == "dashboard":
        simplified_data = simplify_dashboard_data(data, token)
    elif entity == "dataset":
        simplified_data = simplify_dataset_data(data)
        if dataset_exists(simplified_data["table_name"], token):
            print(f"Dataset {simplified_data['table_name']} already exists. Skipping import.")
            return
    else:
        raise ValueError(f"Unknown entity type: {entity}")

    # import entity in Superset
    response = requests.post(f"{BASE_API_URL}/{entity}/", headers=headers, cookies=cookies, json=simplified_data)
    response.raise_for_status()
    print(f"Import successful: {response.json()}")


if __name__ == "__main__":
    # sort files from export folder by their number
    files = sorted(
        [os.path.basename(file) for file in glob.glob(os.path.join(EXPORT_FOLDER, '*.json'))],
        key=lambda x: [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', x)]
    )

    for file in files:
        entity_type = file.split('_')[0]
        entity_path = os.path.join(EXPORT_FOLDER, file)
        import_entity(entity_type, entity_path)
