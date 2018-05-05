import aiohttp

async def post(session, content):
    """Upload content to hastebin.
    :param session: aiohttp ClientSession to use or new
    :param content: content to upload
    :returns: url to post or error
    """ 
    if not session:
        session = aiohttp.ClientSession()
     
    async with session.post("https://hastebin.com/documents", data=content.encode("utf-8")) as resp:
        if resp.status == 200:
            data = await resp.json()
            return "https://hastebin.com/{}".format(data["key"])
        else:
            return f"Error with Hastebin. Server reported error code {resp.status} - RIP."
