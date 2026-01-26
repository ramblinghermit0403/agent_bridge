import asyncio
from app.database.database import AsyncSessionLocal
from app.models.settings import McpServerSetting
from sqlalchemy import select
import json

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(McpServerSetting))
        settings = result.scalars().all()
        for s in settings:
            if True:
                print(f"--- Server: {s.server_name} (ID: {s.id}) ---")
                if s.credentials:
                    creds = json.loads(s.credentials)
                    print(f"Has Access Token: {'Yes' if creds.get('access_token') else 'No'}")
                    print(f"Has Refresh Token: {'Yes' if creds.get('refresh_token') else 'NO'}")
                    if creds.get('expires_at'):
                        import datetime
                        exp = datetime.datetime.fromtimestamp(creds['expires_at'])
                        print(f"Expires At: {exp}")
                    else:
                        print("Expires At: Never (or not set)")
                    
                    if creds.get("oauth_config"):
                        print("OAuth Config Saved:")
                        cfg = creds["oauth_config"]
                        print(f"  - Client ID: {cfg.get('client_id')}")
                        print(f"  - Token URL: {cfg.get('token_url')}")
                        print(f"  - Auth URL: {cfg.get('authorization_url')}")
                        # Don't print secret fully for security, just presence
                        print(f"  - Client Secret: {'***' if cfg.get('client_secret') else 'Missing'}")
                    else:
                        print("OAuth Config: MISSING!")
                else:
                    print("No credentials stored.")
            else:
                print(f"Found Server: {s.server_name} (Not GitHub)")

if __name__ == "__main__":
    asyncio.run(check())
