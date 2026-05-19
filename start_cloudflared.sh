#!/data/data/com.termux/files/usr/bin/bash

echo "Iniciando server..."
python server.py &

sleep 3

echo "Iniciando cloudflared..."
cloudflared tunnel --url http://localhost:8000 > cloudflared.log 2>&1 &

sleep 5

echo "Link:"
grep -o 'https://.*trycloudflare.com' cloudflared.log | head -n 1
