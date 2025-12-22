import os
from dotenv import load_dotenv

load_dotenv()

print("Current environment variables:")
print(f"NOTION_CLIENT_ID: {os.getenv('NOTION_CLIENT_ID')}")
print(f"NOTION_CLIENT_SECRET: {os.getenv('NOTION_CLIENT_SECRET')}")

print("\n\nExpected values (from registration):")
print(f"NOTION_CLIENT_ID: 4WKZy1xb3mPkjpNG")
print(f"NOTION_CLIENT_SECRET: Ln3izUXcJRHtu0BgfLUO8qUh4C4pWWgz")
