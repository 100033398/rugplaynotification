
import asyncio, json, requests, websockets
TRADE_THRESHOLD = 50000.0
WS = "wss://ws.rugplay.com"
TOPIC = ""  # Replace with your ntfy topic (ntfy.sh)

def format_dollars(amount):
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M$"
    elif amount >= 1_000:
        return f"{amount / 1_000:.1f}K$"
    else:
        return f"{amount:.0f}$"

def format_tokens(amount):
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"{amount / 1_000:.1f}K"
    else:
        return f"{amount:.1f}"

def notif(title, msg, tags="rugplay"):
    try:
        requests.post(
            f"https://ntfy.sh/{TOPIC}",
            data=msg.encode(),
            headers={"Title": title.encode(), "Tags": tags}
        )
        print("notif sent:", title)
    except Exception as e:
        print("err sending notif:", e)

async def monitor():
    print(f"watching trades over ${TRADE_THRESHOLD} lol")
    while True:
        try:
            async with websockets.connect(WS, ping_interval=None, ping_timeout=None) as ws:
                print("ws connected")
                await ws.send(json.dumps({"type": "set_coin", "coinSymbol": "@global"}))
                async for m in ws:
                    try:
                        d = json.loads(m)
                        if d.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong"}))
                            continue
                        if d.get("type") != "all-trades":
                            continue
                        t = d.get("data", {})
                        val = float(t.get("totalValue", 0))
                        if val < TRADE_THRESHOLD:
                            continue
                        kind = t.get("type", "")
                        usr = t.get("username", "???")
                        sym = t.get("coinSymbol", "???")
                        amnt = float(t.get("amount", 0))
                        cash = format_dollars(val)
                        tokens = format_tokens(amnt)

                        if kind == "BUY":
                            ttl = f"🟩HUGE BUY: {sym}"
                            body = f"{tokens} Tokens bought for {cash} by @{usr} https://rugplay.com/coin/{sym}"
                        elif kind == "SELL":
                            ttl = f"🟥HUGE SELL: {sym}"
                            body = f"{tokens} Tokens sold for {cash} by @{usr} https://rugplay.com/coin/{sym}"
                        else:
                            continue

                        notif(ttl, body)
                    except:
                        continue
        except:
            print("RIP ws, retrying...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("cya")