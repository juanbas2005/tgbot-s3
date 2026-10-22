#!/usr/bin/env bash
# reproducir el arranque de render localmente con sesion nueva y ver errores
cd ~/tgbot-render && rm -f bot.session* && API_ID=14681595 API_HASH=a86730aab5c59953c424abb4396d32d5 BOT_TOKEN="8544918906:AAERixcFtpR6A7qHi3yTmhSKn8o2tcSv-mk" OWNER_ID=7970466590 PORT=10000 python3 bot.py > render_sim.log 2>&1 &
echo $! > /data/data/com.termux/files/usr/tmp/pid 2>/dev/null || true
sleep 40
curl -s -o /dev/null -w "health: %{http_code}\n" --max-time 5 http://127.0.0.1:10000/
echo "--- log sim:"; cat render_sim.log || true
