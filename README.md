# Deepgram Medical Assistant Voice Bot

A voice-enabled medical assistant that connects Twilio phone calls to a Deepgram AI agent.

## Setup

1. **Install dependencies**
   ```bash
   uv install websockets python-dotenv
   ```

2. **Add your API key**
   Create a `.env` file:
   ```
   DEEPGRAM_API_KEY=your_key_here
   ```

3. **Run the server**
   ```bash
   uv run ./main.py
   ```

## How the Code Works

The application has three main async functions running concurrently:

**`twilio_receiver`** - Receives audio from phone calls
- Listens for Twilio WebSocket messages
- Buffers incoming audio chunks (160 bytes = 20ms of μ-law audio)
- Puts audio chunks in a queue for processing

**`sts_sender`** - Sends audio to Deepgram
- Takes audio chunks from the queue
- Forwards them to Deepgram's agent API via WebSocket

**`sts_receiver`** - Gets AI responses back
- Receives text messages and audio from Deepgram
- Handles "barge-in" events (when user starts speaking)
- Sends synthesized speech back to Twilio

### Key Functions

- `handle_barge_in()` - Sends "clear" message to stop current audio playback
- `load_config()` - Loads the AI agent configuration from JSON
- `sts_connect()` - Creates authenticated WebSocket connection to Deepgram

### Audio Flow
```
Phone → Twilio → Your Server → Deepgram → AI Response → Back to Phone
```

The server acts as a bridge, converting between Twilio's format and Deepgram's agent API while handling real-time audio streaming and conversation management.
