from dotenv import load_dotenv
import os

load_dotenv()

cid = os.environ.get("GITHUB_CLIENT_ID")
csec = os.environ.get("GITHUB_CLIENT_SECRET")

print(f"GITHUB_CLIENT_ID present: {bool(cid)}")
print(f"GITHUB_CLIENT_ID value first 4 chars: {cid[:4] if cid else 'None'}")
print(f"GITHUB_CLIENT_SECRET present: {bool(csec)}")
