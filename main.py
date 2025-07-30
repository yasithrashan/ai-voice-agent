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

