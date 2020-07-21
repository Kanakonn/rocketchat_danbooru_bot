Rocketchat Danbooru Bot
===

Small script to post a random image from danbooru to a rocket.chat server room.

Usage
---
First copy and modify the default config. Use a user ID and auth token from the Personal Access Tokens page in your rocketchat account. Use the API token from your danbooru account.
Setup the channel that it needs to post to and the directory the images should be downloaded to.
Change the image server URL to your webserver (hosting is not provided by the bot). Fill in the tags list with the tags to filter for.
```bash
cp config.json.default config.json
```
Install the necessary requirements
```bash
pip install -r requirements.txt
```
Then run the script.
```bash
python post_image.py
```
The script will post one image each time it is run. There is no checking for duplicates.