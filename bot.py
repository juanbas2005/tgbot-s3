# ponytail: Render usa Python 3.14, donde pyrogram exige un event loop existente
# antes de importar; se crea aqui. Si no hay loop (entorno congelado), fall-back a get_event_loop.
import asyncio
import json
import os
import threading
from pathlib import Path
from urllib.parse import quote

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())

import requests
from pyrogram import Client, filters

ROOT_IDS = {int(os.environ["OWNER_ID"])}
BASE = "https://s3.todus.cu/stream"
REG_FILE = Path("/tmp/files.json")
REG = json.loads(REG_FILE.read_text()) if REG_FILE.exists() else {}

app = Client(
    "bot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"],
)

root = filters.user(*ROOT_IDS)


def save_reg():
    REG_FILE.write_text(json.dumps(REG, indent=2))


@app.on_message(root & filters.command("start"))
def start(_, msg):
    msg.reply("Root ✅\nEnvíame cualquier archivo y lo subo a S3.\n"
              "/files — listar · /rm <nombre> — borrar · /ping")


@app.on_message(root & filters.command("ping"))
def ping(_, msg):
    msg.reply("pong")


@app.on_message(root & filters.command("files"))
def files(_, msg):
    msg.reply("\n".join(f"• {n}" for n in REG) or "Sin archivos")


@app.on_message(root & filters.command("rm"))
def rm(_, msg):
    if len(msg.command) < 2:
        return msg.reply("Uso: /rm <nombre>")
    name = " ".join(msg.command[1:])
    if name not in REG:
        return msg.reply("No está en la lista (/files)")
    r = requests.delete(REG[name], timeout=30)
    if r.status_code in (200, 204, 404):
        REG.pop(name)
        save_reg()
        msg.reply(f"🗑 Borrado ({r.status_code})")
    else:
        msg.reply(f"⚠️ DELETE devolvió {r.status_code}")


@app.on_message(root & filters.media)
def upload(_, msg):
    status = msg.reply("⏳ Procesando…")
    path = None
    try:
        path = msg.download()
        name = os.path.basename(path)
        url = f"{BASE}/GRATIS/tg_{msg.from_user.id}/{quote(name, safe='')}"
        status.edit(f"⏳ Subiendo {name}…")
        with open(path, "rb") as f:
            r = requests.put(url, data=f, timeout=(10, 600))
        head = requests.head(url, timeout=30)
        if r.status_code in (200, 201) and head.status_code == 200:
            REG[name] = url
            save_reg()
            status.edit(f"✅ {url}")
        else:
            status.edit(f"⚠️ PUT {r.status_code} / HEAD {head.status_code}")
    except Exception as e:
        status.edit(f"❌ {e}")
    finally:
        if path and os.path.exists(path):
            os.remove(path)


@app.on_message(~root)
def deny(_, msg):
    msg.reply("⛔ Solo root")


def _http_server():
    # ponytail: Render free exige responder en $PORT o mata el deploy
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Health(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    port = int(os.environ.get("PORT", "0"))
    if port:
        threading.Thread(
            target=HTTPServer(("0.0.0.0", port), Health).serve_forever,
            daemon=True,
        ).start()


if __name__ == "__main__":
    import time

    _http_server()
    app.start()
    app.send_message(*ROOT_IDS, "Bot funcionando ✅ (Render)")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        time.sleep(2)
