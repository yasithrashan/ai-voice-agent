import asyncio
import base64
import json
import sys
import websockets
import ssl
import os

from dotenv import load_dotenv
load_dotenv() 


def sts_connect():
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )
    return sts_ws


def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)


async def handle_barge_in(decoded, twilio_ws, streamsid):
    pass


async def handle_text_message(decoded, twilio_ws, streamsid):
    pass


async def sts_sender(sts_ws, audio_queue):
    pass


async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    pass


async def twillio_reciver(twilio_ws, audio_queue, streamsid_queue):
    BUFFER_SIZE = 20 * 160
    inbuffer = bytearray(BUFFER_SIZE)

    async for message in twilio_ws:
        try:
            data = json.loads(message)
            event = data.get('event')

            if event == 'start':
                print("Twilio stream started")
                start = data['start']
                streamsid = start['streamSid']
                streamsid_queue.put_nowait(streamsid)

            elif event == 'connected':
                print("Twilio connected")
                continue

            elif event == 'media':
                print("Twilio media received")
                media = data['media']
                chunk = base64.b64decode(media['payload'])
                if media["track"] == "inbound":
                    inbuffer.extend(chunk)

            elif event == 'stop':
                break

            while len(inbuffer) >= BUFFER_SIZE:
                chunk = inbuffer[:BUFFER_SIZE]
                audio_queue.put_nowait(chunk)
                inbuffer = inbuffer[BUFFER_SIZE:]

        except Exception as e:
            print(f"Error: {e}")
            break


async def twilo_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        config_message = load_config()
        await sts_ws.send(json.dumps(config_message))

        await asyncio.gather(
            asyncio.ensure_future(sts_sender(sts_ws, audio_queue)),
            asyncio.ensure_future(sts_receiver(sts_ws, twilio_ws, streamsid_queue)),
            asyncio.ensure_future(twillio_reciver(twilio_ws, audio_queue, streamsid_queue))
        )
        await twilio_ws.close()


async def main():
    await websockets.serve(twilo_handler, "localhost", 5000)
    print("Server started on ws://localhost:5000")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
