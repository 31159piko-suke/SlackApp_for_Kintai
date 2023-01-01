import os
import json
import logging
from typing import Dict, List
import requests


API_SECRET = os.environ.get("API_SECRET")
HEADERS = {
    "Authorization": f"Bearer {API_SECRET}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_pages_from_database(database_id: str) -> Dict:
    res = requests.post(
        url=f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=HEADERS,
    )
    if res.status_code == 200:
        logging.info("get_pages_from_database: success!")
        return res.json()["results"]
    else:
        logging.error(f"get_pages_from_database: {res.json()}")
        raise Exception("Failed to get pages info from database.")


def create_page(
    database_id: str,
    tags: List[str] = [],
    title: str = "Title",
) -> None:
    URL = os.environ.get("URL")
    body = {
        "parent": {"database_id": database_id},
        "icon": {"emoji": "🚀"},
        "cover": {"external": {"url": URL}},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Tags": {"multi_select": [{"name": i} for i in tags]},
            "Time": {"number": 0},
        },
    }
    res = requests.post(
        url=f"https://api.notion.com/v1/pages",
        data=json.dumps(body),
        headers=HEADERS,
    )
    if res.status_code == 200:
        logging.info("create_page: success!")
    else:
        logging.error(f"create_page: {res.json()}")
        raise Exception("Failed to create page.")


def add_progress(
    page_id: str,
    progress: Dict[str, str],
) -> None:
    def _contents(tag: str, progress: str) -> List[Dict]:
        return [
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": tag}}]},
            },
            {
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": progress}}]},
            },
        ]

    body = {
        "children": sum([_contents(k, v) for k, v in progress.items()], []),
    }

    res = requests.patch(
        url=f"https://api.notion.com/v1/blocks/{page_id}/children",
        data=json.dumps(body),
        headers=HEADERS,
    )
    if res.status_code == 200:
        logging.info("add_progress: success!")
    else:
        logging.error(f"add_progress: {res.json()}")
        raise Exception("Failed to update page.")


def update_tags_property(
    page_id: str,
    tags=List[str],
) -> None:
    def _get_tags_property(page_id: str) -> List[str]:
        res = requests.get(
            url=f"https://api.notion.com/v1/pages/{page_id}/properties/Tags",
            headers=HEADERS,
        )
        if res.status_code == 200:
            logging.info("get_tags_property: success!")
            return [r["name"] for r in res.json()["multi_select"]]
        else:
            logging.error(f"get_tags_property: {res.json()}")
            raise Exception("Not found the page.")

    exsisted_tags: List[str] = _get_tags_property(page_id)

    body = {
        "properties": {
            "Tags": {"multi_select": [{"name": i} for i in exsisted_tags + tags]},
        }
    }
    res = requests.patch(
        url=f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body),
        headers=HEADERS,
    )
    if res.status_code == 200:
        logging.info("update_page: success!")
    else:
        logging.error(f"update_tags_property: {res.json()}")
        raise Exception("Failed to add tags property.")


def update_time_property(
    page_id: str,
    time: int,
) -> None:
    def _get_time_property(page_id: str) -> int:
        res = requests.get(
            url=f"https://api.notion.com/v1/pages/{page_id}/properties/Time",
            headers=HEADERS,
        )
        if res.status_code == 200:
            return res.json()["number"]
        else:
            raise Exception("Not found the page.")

    cumulative_time: int = _get_time_property(page_id)

    body = {
        "properties": {
            "Time": {"number": cumulative_time + time},
        }
    }
    res = requests.patch(
        url=f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body),
        headers=HEADERS,
    )
    if res.status_code == 200:
        logging.info("update_property: success!")
    else:
        logging.error(f"update_tags_property: {res.json()}")
        raise Exception("Failed to add time property.")
