import os
import sys
import heroku3
import git
import asyncio
from config import bot, call_py, HNDLR, contact_filter, ON_HEROKU, UPSTREAM, HEROKU_API_KEY, HEROKU_APP_NAME
from pyrogram import Client, filters
from pyrogram.types import Message


REPO_REMOTE_NAME = "upstream"

async def restart(client, message):
    await client.restart()
    await message.edit(f"**Restarted!** \nDo `{HNDLR}ping` to check if it's Online!!")
    
async def exec(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout , stderr= await process.communicate()
    return stdout.decode()


@Client.on_message(contact_filter & filters.command(['update'], prefixes=f"{HNDLR}"))
async def updater(client, m: Message):
   haha = await m.reply("`...`")
   try:
      repo = git.Repo()
   except git.exc.InvalidGitRepositoryError as er:
      repo = git.Repo.init()
      origin = repo.create_remote(REPO_REMOTE_NAME, UPSTREAM)
      origin.fetch()
      repo.create_head("video", origin.refs.video)
      repo.heads.video.checkout(True)
   repo.remote(REPO_REMOTE_NAME).fetch("video")
   
   if ON_HEROKU:
      try:
         heroku = heroku3.from_key(HEROKU_API_KEY)
         heroku_applications = heroku.apps()
         heroku_app = None
         for app in heroku_applications:
            if app.name == HEROKU_APP_NAME:
               heroku_app = app
               break
         if heroku_app:
            await haha.edit("Build in Progress... \nPlease wait for a few minutes till we update and restart your app.")
            heroku_git_url = heroku_app.git_url.replace(
               "https://",
               "https://api:" + HEROKU_API_KEY + "@"
            )
            print(heroku_git_url)
            if "heroku" in repo.remotes:
               remote = repo.remote("heroku")
               print(remote.set_url(heroku_git_url))
            else:
               remote = repo.create_remote("heroku", heroku_git_url)
               print(remote)
            print(remote.push(refspec="HEAD:refs/heads/video", force=True))
            asyncio.get_event_loop().create_task(restart(client, haha))
         else:
            await haha.edit("Check your `HEROKU_APP_NAME` in Vars and try again.")
      except:
         await haha.edit("Check your `HEROKU_API_KEY` in Vars and try again.")
          
   else:
      hmm = await exec("git pull -f")
      await exec("pip3 install -r requirements.txt")
      await haha.edit(f"`{hmm}`")
      await client.disconnect()
      os.execl(sys.executable, "python3", "-m", "main.py")
      
      
   
      
