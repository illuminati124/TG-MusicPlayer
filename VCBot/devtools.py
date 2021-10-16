import traceback
import sys
import os
import re
import subprocess
import io
import asyncio
from io import StringIO
from config import HNDLR, contact_filter, bot
from pyrogram import Client, filters
from pyrogram.types import Message

async def aexec(code, client, m):
    c = m.chat.id
    message = m
    rm = m.reply_to_message
    if m.reply_to_message:
        id = m.reply_to_message.message_id
    else:
        id = m.message_id
    exec(
        f"async def __aexec(client, m, c, rm, message, id): "
        + "".join(f"\n {l}" for l in code.split("\n"))
    )
    return await locals()["__aexec"](client, m, c, rm, message, id)

p = print

@Client.on_message(contact_filter & filters.command('eval', prefixes=f'{HNDLR}'))
async def evaluate(client, m: Message):
    status_message = await m.reply_text("`Running ...`")
    try:
        cmd = m.text.split(" ", maxsplit=1)[1]
    except IndexError:
        await status_message.delete()
        return
    reply_to_id = m.message_id
    if m.reply_to_message:
        reply_to_id = m.reply_to_message.message_id
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, client, m)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = f"<b>Command:</b>\n<code>{cmd}</code>\n\n<b>Output</b>:\n<code>{evaluation.strip()}</code>"
    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(str(final_output))
        await m.reply_document(
            document=filename,
            caption=f"Output.txt",
            disable_notification=True,
            reply_to_message_id=reply_to_id,
        )
        os.remove(filename)
        await status_message.delete()
    else:
        await status_message.edit(final_output)
        
        
p = print

@Client.on_message(contact_filter & filters.command('bash', prefixes=f'{HNDLR}'))
async def terminal(client, m: Message):
    shtxt = await m.reply_text("`Processing...`")
    try: 
        cmd = m.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await shtxt.edit("`No cmd given`")
    
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    OUT = f"**☞ BASH\n\n• COMMAND:**\n`{cmd}` \n\n"
    e = stderr.decode()
    if e:
        OUT += f"**• ERROR:** \n`{e}`\n\n"
    t = stdout.decode()
    if t:
        _o = t.split("\n")
        o = "\n".join(_o)
        OUT += f"**• OUTPUT:**\n`{o}`"
    if not e and not t:
        OUT += f"**• OUTPUT:**\n`Success`"
    if len(OUT) > 4096:
        ultd = OUT.replace("`", "").replace("*", "").replace("_", "")
        with io.BytesIO(str.encode(ultd)) as out_file:
            out_file.name = "bash.txt"
            await m.reply_document(
                document=out_file,
                caption=f"Bash.txt",
                reply_to_message_id=m.message_id
            )
            await shtxt.delete()
    else:
        await shtxt.edit(OUT)  
