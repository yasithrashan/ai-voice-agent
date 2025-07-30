import asyncio
import base64
import json
import os
import websockets

from dotenv import load_dotenv
load_dotenv()


def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)


async def sts_connect():
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

    return websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        extra_headers={"Authorization": f"Token {api_key}"}
    )


async def handle_barge_in(decoded, twilio_ws, streamsid):
    if decoded.get("type") == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": streamsid
        }
        await twilio_ws.send(json.dumps(clear_message))


async def handle_text_message(decoded, twilio_ws, streamsid):
    await handle_barge_in(decoded, twilio_ws, streamsid)


async def sts_sender(sts_ws, audio_queue):
    print("Starting STS sender")
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk)


async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    print("Starting STS receiver")
    streamsid = await streamsid_queue.get()

    async for message in sts_ws:
        if isinstance(message, str):
            print(f"Received message: {message}")
            decoded = json.loads(message)
            await handle_text_message(decoded, twilio_ws, streamsid)
        else:
            raw_mulaw = message
            media_message = {
                "event": "media",
                "streamSid": streamsid,
                "media": {
                    "payload": base64.b64encode(raw_mulaw).decode('ascii'),
                }
            }
            await twilio_ws.send(json.dumps(media_message))


async def twilio_receiver(twilio_ws, audio_queue, streamsid_queue):
    BUFFER_SIZE = 20 * 160
    inbuffer = bytearray()

    async for message in twilio_ws:
        try:
            data = json.loads(message)
            event = data.get('event')

            if event == 'start':
                print("Twilio stream started")
                streamsid = data['start']['streamSid']
                streamsid_queue.put_nowait(streamsid)

            elif event == 'connected':
                print("Twilio connected")

            elif event == 'media':
                print("Twilio media received")
                media = data['media']
                chunk = base64.b64decode(media['payload'])
                if media["track"] == "inbound":
                    inbuffer.extend(chunk)

            elif event == 'stop':
                print("Twilio stream stopped")
                break

            while len(inbuffer) >= BUFFER_SIZE:
                chunk = inbuffer[:BUFFER_SIZE]
                audio_queue.put_nowait(chunk)
                inbuffer = inbuffer[BUFFER_SIZE:]

        except Exception as e:
            print(f"Error in Twilio receiver: {e}")
            break


async def twilio_handler(twilio_ws, path):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with await sts_connect() as sts_ws:
        config_message = load_config()
        await sts_ws.send(json.dumps(config_message))

        await asyncio.gather(
            sts_sender(sts_ws, audio_queue),
            sts_receiver(sts_ws, twilio_ws, streamsid_queue),
            twilio_receiver(twilio_ws, audio_queue, streamsid_queue)
        )

        await twilio_ws.close()
        await sts_ws.close()


async def main():
    server = await websockets.serve(twilio_handler, "localhost", 5000)
    print("Server started on ws://localhost:5000")
    await asyncio.Future()  # Keeps the server running


if __name__ == "__main__":
    asyncio.run(main())
