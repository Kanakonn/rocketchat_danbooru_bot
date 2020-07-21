import json
import os
import sys

import requests
from requests import sessions
from requests.auth import HTTPBasicAuth
from rocketchat_API.rocketchat import RocketChat

DANBOORU_POSTS_URL = "https://danbooru.donmai.us/posts.json"
DANBOORU_POST_URL = "https://danbooru.donmai.us/posts/{id}"
PIXIV_POST_URL = "https://www.pixiv.net/en/artworks/{id}"

CONFIG = {}
DANBOORU_HEADERS = {}
ROCKETCHAT_HEADERS = {}


def get_danbooru_image(tags):
    auth = HTTPBasicAuth(CONFIG['danbooru_username'], CONFIG['danbooru_api_key'])
    image = requests.get(DANBOORU_POSTS_URL, params={
        "limit": 1,
        "random": "true",
        "tags": tags
    }, auth=auth)
    return image.json()

def download_danbooru_image(image):
    attachment_data = requests.get(image["file_url"])
    if attachment_data.status_code == 200:
        filename = "{}.{}".format(image['md5'], image['file_ext'])
        with open(os.path.join(CONFIG['download_dir'], filename), 'wb') as f:
            f.write(attachment_data.content)
        return filename
    else:
        raise ValueError("Could not download {}: {} {}".format(image['file_url'], attachment_data.status_code, attachment_data.content))

if __name__ == "__main__":
    try:
        with open("config.json", 'r') as f:
            CONFIG = json.loads("".join(f.readlines()))
    except FileNotFoundError as e:
        print("Config file config.json not found, copy config.json.default and modify!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print("Invalid configuration file, check config.json")
        sys.exit(2)

    if not all(x in CONFIG.keys() for x in [
        "danbooru_username", "danbooru_api_key", "rocketchat_server", "rocketchat_user_id",
        "rocketchat_auth_token", "rocketchat_rate_limit_ms", "rocketchat_channel", "download_dir",
        "image_server_url", "tags"
    ]):
        print("Missing one or more required config keys!")
        sys.exit(3)

    if not os.path.isdir(CONFIG['download_dir']):
        os.makedirs(CONFIG["download_dir"])

    tags = " ".join(CONFIG['tags'])
    image = get_danbooru_image(tags)
    if isinstance(image, list):
        image = image[0]

    try:
        image_filename = download_danbooru_image(image)
    except Exception as e:
        print("Error downloading image: {}".format(e))
        print(image)
        raise e

    image_url = CONFIG['image_server_url'].format(filename=image_filename)

    RATE_LIMIT = CONFIG['rocketchat_rate_limit_ms'] / 1000

    with sessions.Session() as session:
        print("Connecting to rocket.chat instance...")
        print("Rate limiter is set to {} seconds".format(RATE_LIMIT))
        rocketchat = RocketChat(user_id=CONFIG['rocketchat_user_id'], auth_token=CONFIG['rocketchat_auth_token'],
                                server_url=CONFIG['rocketchat_server'], session=session)

        fields = []
        if image['tag_string_artist'] != "":
            fields.append({"short": True, "title": "Artist", "value": image['tag_string_artist']})
        if image['tag_string_copyright'] != "":
            fields.append({"short": True, "title": "Copyright", "value": image['tag_string_copyright']})
        if image['tag_string_character'] != "":
            fields.append({"short": True, "title": "Character", "value": image['tag_string_character']})
        if image['pixiv_id'] not in ["", '""', "null", None]:
            fields.append({"short": True, "title": "Pixiv ID", "value": image['pixiv_id']})
        if image['tag_string_general'] != "":
            fields.append({"short": False, "title": "Tags", "value": image['tag_string_general']})

        print("Posting image #{} to channel {}".format(image['id'], CONFIG['rocketchat_channel']))

        source_url = None
        if source_url is None and image["pixiv_id"] not in ["", '""', "null", None]:
            source_url = PIXIV_POST_URL.format(id=image['pixiv_id'])
        if source_url is None and ("http://" in image["source"] or "https://" in image["source"]):
            source_url = image["source"]
        if source_url is None:
            source_url = DANBOORU_POST_URL.format(id=image['id'])

        res = rocketchat.chat_post_message(text=None, channel=CONFIG['rocketchat_channel'], attachments=[
            {
                "title": "Danbooru #{}".format(image['id']),
                "title_link": source_url,
                "image_url": image_url,
                "fields": fields
            }
        ])
        if res.status_code != 200:
            print("Posting failed! Error {}".format(res.status_code))
            print(res.json())
        else:
            print("Done!")
