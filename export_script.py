from helpers import BASE_API_URL, EXPORT_FOLDER
from helpers import get_authentication_token
import requests
import json
import os


# set default page size for Superset entities
PAGE_SIZE = 25
PAGE_LIMIT = 1000


def fetch_entities(entity, page, page_size):
    """Function for requesting entities by page from Superset."""

    # get authentication token
    token = get_authentication_token()

    # make header request
    headers = {"Authorization": f"Bearer {token}"}

    # get entity from Superset
    response = requests.get(f"{BASE_API_URL}/{entity}?q=(page:{page},page_size:{page_size})", headers=headers)
    response.raise_for_status()
    return response.json()['result']


def export_entity(entity):
    """Function for exporting entity in json files."""

    # export entity as json file in the export folder
    for page in range(PAGE_LIMIT):
        results = fetch_entities(entity, page, PAGE_SIZE)
        if not results:
            break
        for item in results:
            # filter entities by not containing word WIP in name
            if 'WIP' not in item.get('slice_name', ''):
                file_name = f"{entity}_{item['id']}.json"
                with open(os.path.join(EXPORT_FOLDER, file_name), "w") as f:
                    json.dump(item, f, indent=4)


if __name__ == "__main__":
    # create export folder if not exists
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

    # export every superset entity
    for superset_entity in ["dashboard", "chart", "dataset"]:
        export_entity(superset_entity)
