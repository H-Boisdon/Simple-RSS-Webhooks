import argparse
import json
import logging
import os
import time
from typing import Any

import requests
from feedparser import parse

from config.settings import settings
from youtube.youtube import create_discord_payload, extract_youtube_data


def load_data() -> set[str]:
    if not os.path.exists(settings.dataFile):
        return set()
    try:
        with open(settings.dataFile, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()


def save_data(data: set[str]):
    try:
        with open(settings.dataFile, "w", encoding="utf-8") as f:
            json.dump(list(data), f, ensure_ascii=False, indent=4)
    except IOError as e:
        logging.error(f"Failed to save data: {e}")


def clear_data():
    with open(settings.dataFile, "w", encoding="utf-8") as f:
        json.dump([], f)


def send_webhook(entry_data: dict[str, Any]):
    payload = create_discord_payload(entry_data)
    try:
        if settings.env == "dev":
            logging.info(json.dumps(entry_data, ensure_ascii=False, indent=2))
            return
        result = requests.post(settings.webhookUrl, json=payload, timeout=10)
        result.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error(f"Error sending webhook: {err}")


def main():
    parser = argparse.ArgumentParser(description="RSS Webhook Monitor")
    parser.add_argument(
        "--skip-existing",
        "-s",
        action="store_true",
        help="Skip all previously existing items in the feed on the first run",
    )
    parser.add_argument(
        "--clear",
        "-c",
        action="store_true",
        help="Clear all cached items",
    )
    args = parser.parse_args()

    if args.clear:
        clear_data()

    knownIds = load_data()

    # If this is the first run ever, populate seen_ids so we don't spam
    if not knownIds and args.skip_existing:
        feed = parse(str(settings.rssFeedUrl))
        for entry in feed.entries:
            id = entry.link
            if entry.id:
                id = entry.id
            knownIds.add(id)
        save_data(knownIds)
        logging.info(
            f"Initialized. Skipped {len(knownIds)} existing feed items as seen."
        )

    # while True:
    try:
        feed = parse(str(settings.rssFeedUrl))
        if feed.bozo:
            logging.warning("Feed data might be malformed.")

        newItemFound = False

        for entry in reversed(feed.entries):
            id = entry.link
            if entry.id:
                id = entry.id
            if id in knownIds:
                continue

            entry_data = extract_youtube_data(entry)

            logging.info(f"New feed item of id: {id}")
            send_webhook(entry_data)
            knownIds.add(id)
            newItemFound = True
            time.sleep(1)

        if newItemFound:
            save_data(knownIds)

    except Exception as e:
        logging.error(f"Unexpected error:\n{e}\n", exc_info=True)

    # time.sleep(settings.checkInterval)


if __name__ == "__main__":
    main()
