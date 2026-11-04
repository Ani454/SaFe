import json, os
from dotenv import load_dotenv
from mistralai.client import Mistral
from stats import get_neighborhood_stats
from summarize import build_payload

load_dotenv()
client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
print("key ends with:", os.environ["MISTRAL_API_KEY"][-4:])

# 1. How big is the payload?
payload = build_payload(get_neighborhood_stats("Tenderloin", days=30), "Tenderloin", 30)
text = json.dumps(payload, default=str)
print("payload chars:", len(text), "≈ tokens:", len(text) // 4)
print("keys:", list(payload.keys()))

# 2. Does a tiny request work?
r = client.chat.complete(model="mistral-small-latest",
                         messages=[{"role": "user", "content": "Say hi"}])
print("tiny request OK:", r.choices[0].message.content)
