import logging
import httpx
import uuid
import secrets
import hashlib
import base64
import time
import json
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from fastapi import HTTPException


from app.services.redis.redis_client import redis_client

logger = logging.getLogger(__name__)

class MCPAuthService:
    @staticmethod
    async def discover_oauth_config(server_url: str) -> Optional[Dict[str, str]]:
        """
        Implements MCP 'Smart Auth' discovery:
        1. POST to server_url -> 401 + WWW-Authenticate header.
        2. Extract resource_metadata URL.
        3. Fetch metadata -> get OAuth endpoints.
        """
        logger.info(f"Discovering OAuth config for {server_url}")
        
        # 1. Trigger 401
        async with httpx.AsyncClient() as client:
            try:
                # Send dummy JSON-RPC to trigger auth challenge
                dummy_payload = {
                    "jsonrpc": "2.0", 
                    "method": "initialize", 
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "discovery", "version": "1.0"}}, 
                    "id": 1
                }
                resp = await client.post(server_url, json=dummy_payload)
                
                if resp.status_code != 401:
                    logger.warning(f"Expected 401 for discovery, got {resp.status_code}")
                    # Fallback: maybe it's not protected or assumes static config?
                    return None
                
                auth_header = resp.headers.get("www-authenticate", "")
                if not auth_header:
                    return None
                    
                # Parse header: Bearer resource_metadata="https://..."
                metadata_url = None
                found_metadata = False # Initialize here to avoid UnboundLocalError
                parts = auth_header.split(",")
                for part in parts:
                    if "resource_metadata" in part:
                        # Extract URL found between quotes
                        try:
                            metadata_url = part.split('resource_metadata="')[1].split('"')[0]
                        except IndexError:
                            pass
                
                if not metadata_url:
                    logger.warning("No resource_metadata found in WWW-Authenticate header. Trying .well-known fallback...")
                    # Fallback: Try .well-known/oauth-authorization-server at the server root
                    from urllib.parse import urlparse, urljoin
                    parsed = urlparse(server_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    # Try both root and current path (just in case)
                    well_known_paths = [
                        "/.well-known/oauth-authorization-server",
                        f"{parsed.path.rstrip('/')}/.well-known/oauth-authorization-server"
                    ]
                    
                    found_metadata = False
                    for path in well_known_paths:
                         fallback_url = urljoin(base_url, path)
                         logger.info(f"Trying fallback discovery: {fallback_url}")
                         try:
                             meta_resp = await client.get(fallback_url)
                             if meta_resp.status_code == 200:
                                  metadata_url = fallback_url
                                  found_metadata = True
                                  break
                         except Exception:
                             continue
                    
                    if not found_metadata:
                         logger.warning("Failed to discover OAuth config via .well-known fallback.")
                         return None
                    
                logger.info(f"Fetching metadata from {metadata_url}")
                # If we just found it via fallback, we already have certain response, but re-fetching logic is clean for now
                if not found_metadata: # Only fetch if we didn't just check it
                    meta_resp = await client.get(metadata_url)
                    if meta_resp.status_code != 200:
                        logger.error(f"Failed to fetch metadata: {meta_resp.status_code}")
                        return None
                    
                metadata = meta_resp.json()
                
                auth_url = metadata.get("authorization_endpoint")
                token_url = metadata.get("token_endpoint")
                
                # RFC 8414 / GitHub "Smart Auth" Indirection
                if (not auth_url or not token_url) and "authorization_servers" in metadata:
                    auth_servers = metadata.get("authorization_servers", [])
                    for server in auth_servers:
                         # For GitHub specifically, we know the endpoints if the issuer matches, 
                         # because their .well-known/openid-configuration is incomplete.
                         if "github.com" in server:
                             if not auth_url: auth_url = "https://github.com/login/oauth/authorize"
                             if not token_url: token_url = "https://github.com/login/oauth/access_token"
                             break
                             
                         # General recursion logic (simplified)
                         try:
                             # Try openid-configuration as it's more common than oauth-authorization-server for some
                             well_known = f"{server.rstrip('/')}/.well-known/openid-configuration"
                             logger.info(f"Fetching indirect config: {well_known}")
                             ind_resp = await client.get(well_known)
                             if ind_resp.status_code == 200:
                                 ind_meta = ind_resp.json()
                                 if not auth_url: auth_url = ind_meta.get("authorization_endpoint")
                                 if not token_url: token_url = ind_meta.get("token_endpoint")
                         except Exception:
                             pass
                             
                         if auth_url and token_url:
                             break

                return {
                    "authorization_url": auth_url,
                    "token_url": token_url
                }
                
            except Exception as e:
                logger.error(f"Discovery error: {e}")
                return None

    @classmethod
    async def init_oauth_flow(cls, server_name: str, redirect_uri: str, client_id: Optional[str] = None, client_secret: Optional[str] = None, server_url: Optional[str] = None, scope: Optional[str] = None, authorization_url: Optional[str] = None, token_url: Optional[str] = None) -> str:
        
        if not server_url:
             raise HTTPException(status_code=400, detail="Server URL is required for connection.")
        
        # 1. Try Dynamic Discovery (unless manual config provided for BOTH endpoints)
        discovered_config = await cls.discover_oauth_config(server_url)
        d_config = discovered_config or {}
    
        # Logic: Manual Override > Discovered
        auth_url_base = authorization_url or d_config.get('authorization_url')
        final_token_url = token_url or d_config.get('token_url')
        
        # Validation relaxed: token_url is optional for init
        if not auth_url_base:
            logger.error(f"Missing Config. Auth: {auth_url_base}, Token: {final_token_url}")
            raise HTTPException(status_code=400, detail="Could not determine OAuth configuration. Please provide 'Authorization URL' manually in Advanced Options.")
            
        # Get Credentials
        if not client_id:
            raise HTTPException(status_code=400, detail="Client ID missing. Please register the app with the provider and enter the Client ID.")
        
        final_scope = scope if scope else ""

        # Generate PKCE parameters (required for OAuth 2.1)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        state = str(uuid.uuid4())
        
        # Store state in Redis with 10 minute expiry
        state_data = {
            "client_id": client_id,
            "client_secret": client_secret, 
            "redirect_uri": redirect_uri,
            "authorization_url": auth_url_base, # Persist for saving later
            "token_url": final_token_url,
            "server_url": server_url,
            "server_name": server_name,
            "scope": final_scope,
            "code_verifier": code_verifier 
        }
        redis_client.setex(f"oauth_state:{state}", 600, json.dumps(state_data))
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        if final_scope:
            params["scope"] = final_scope
        
        # Notion requires owner=user parameter (Legacy workaround, keep if possible or move to frontend presets?)
        # Since we removed preapproved list, we can check server_name loosely or url host
        if "notion" in server_url.lower() or "notion" in server_name.lower():
            params["owner"] = "user"
        
        auth_url = f"{auth_url_base}?{urlencode(params)}"
        return auth_url

    @classmethod
    async def finalize_oauth_flow(cls, code: str, state: str):
        print(f"DEBUG: Finalize called with code={code}, state={state}")
        
        # Retrieve from Redis
        stored_state_json = redis_client.get(f"oauth_state:{state}")
        if not stored_state_json:
            print("DEBUG: State not found in redis")
            raise HTTPException(status_code=400, detail="Invalid or expired state")
            
        stored_state = json.loads(stored_state_json)
        # Delete used state
        redis_client.delete(f"oauth_state:{state}")
        
        print(f"DEBUG: Found state. Token URL: {stored_state['token_url']}")

        server_url = stored_state['server_url'] 
        server_name = stored_state.get('server_name', 'Custom Server')

        # Exchange code for token
        async with httpx.AsyncClient() as client:
            try:
                # Figma/GitHub use Basic Auth, Notion uses client credentials in body
                auth = httpx.BasicAuth(stored_state['client_id'], stored_state['client_secret']) if stored_state.get('client_secret') else None
               
                data = {
                    "redirect_uri": stored_state['redirect_uri'],
                    "code": code,
                    "grant_type": "authorization_code",
                }
               
                # Add PKCE code_verifier
                if "code_verifier" in stored_state:
                    data["code_verifier"] = stored_state['code_verifier']
               
                print(f"DEBUG: Sending token request to {stored_state['token_url']}")
               
                # Some providers require client_id in body even if not basic auth (public clients)
                if not auth:
                    data['client_id'] = stored_state['client_id']

                resp = await client.post(
                    stored_state['token_url'], 
                    data=data, 
                    auth=auth,
                    headers={"Accept": "application/json"}
                )
               
                print(f"DEBUG: Token response status: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"DEBUG: Token response body: {resp.text}")
                    logger.error(f"Token exchange failed: {resp.text}")
                    raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")

                token_data = resp.json()
                
                # Calculate expiry
                expires_in = token_data.get("expires_in", 3600) # Default 1 hour
                expires_at = int(time.time()) + expires_in

                # Build credentials with expiry info AND OAUTH CONFIG
                credentials_dict = {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": expires_at,
                    "token_type": token_data.get("token_type", "Bearer"),
                    "oauth_config": {
                        "client_id": stored_state['client_id'],
                        "client_secret": stored_state.get('client_secret'),
                        "authorization_url": stored_state.get('authorization_url'),
                        "token_url": stored_state['token_url'],
                        "scope": stored_state.get('scope')
                    }
                }
                
                credentials_json = json.dumps(credentials_dict)
                print(f"DEBUG: Token exchanged successfully. Expires at: {expires_at}")
                
                return {
                    "server_name": server_name,
                    "server_url": server_url,
                    "credentials": credentials_json
                }
                   
            except HTTPException:
                raise # Re-raise FastAPI HTTP exceptions
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Error during token exchange: {e}")
                raise HTTPException(status_code=500, detail=f"Internal error during token exchange: {e}")
    @staticmethod
    async def inspect_server(server_url: str) -> Dict[str, Any]:
        """
        Probes a server for MCP authentication metadata and returns a detailed diagnostic report.
        """
        report = {
            "server_url": server_url,
            "header_probe": {"status": "skipped", "details": None, "data": None},
            "well_known_probe": {"status": "skipped", "details": None, "data": None},
            "discovered_config": None
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Header Probe
            try:
                # Send dummy JSON-RPC to trigger auth challenge
                dummy_payload = {
                    "jsonrpc": "2.0", 
                    "method": "initialize", 
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "inspector", "version": "1.0"}}, 
                    "id": 1
                }
                resp = await client.post(server_url, json=dummy_payload)
                report["header_probe"]["http_status"] = resp.status_code
                report["header_probe"]["www_authenticate"] = resp.headers.get("www-authenticate")
                
                if resp.status_code == 401:
                    auth_header = resp.headers.get("www-authenticate", "")
                    if auth_header:
                        report["header_probe"]["status"] = "found_header"
                        # Parse header
                        parts = auth_header.split(",")
                        for part in parts:
                            if "resource_metadata" in part:
                                try:
                                    meta_url = part.split('resource_metadata="')[1].split('"')[0]
                                    report["header_probe"]["metadata_url"] = meta_url
                                    
                                    # Fetch
                                    meta_resp = await client.get(meta_url)
                                    if meta_resp.status_code == 200:
                                        report["header_probe"]["data"] = meta_resp.json()
                                        report["header_probe"]["status"] = "success"
                                        report["discovered_config"] = {
                                            "authorization_url": report["header_probe"]["data"].get("authorization_endpoint"),
                                            "token_url": report["header_probe"]["data"].get("token_endpoint")
                                        }
                                    else:
                                        report["header_probe"]["details"] = f"Failed to fetch metadata URL: {meta_resp.status_code}"
                                except Exception as e:
                                    report["header_probe"]["details"] = f"Parsing error: {str(e)}"
                    else:
                        report["header_probe"]["details"] = "401 received but no WWW-Authenticate header"
                        report["header_probe"]["status"] = "failed"
                else:
                    report["header_probe"]["details"] = f"Expected 401, got {resp.status_code}"
                    report["header_probe"]["status"] = "failed"
            except Exception as e:
                report["header_probe"]["status"] = "error"
                report["header_probe"]["details"] = str(e)

            # 2. Well-Known Probe (Run even if header succeeded to be thorough, or only if failed? User wants "discover every config")
            # Let's run it always for the inspector tool.
            try:
                from urllib.parse import urlparse, urljoin
                parsed = urlparse(server_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                well_known_paths = [
                    "/.well-known/oauth-authorization-server",
                    f"{parsed.path.rstrip('/')}/.well-known/oauth-authorization-server",
                    "/.well-known/openid-configuration"
                ]
                
                param_data = {}
                for path in well_known_paths:
                    fallback_url = urljoin(base_url, path)
                    try:
                        meta_resp = await client.get(fallback_url)
                        if meta_resp.status_code == 200:
                            data = meta_resp.json()
                            param_data[path] = {"found": True, "data": data}
                            
                            # Update config if not already found by header
                            if not report["discovered_config"]:
                                report["discovered_config"] = {
                                    "authorization_url": data.get("authorization_endpoint"),
                                    "token_url": data.get("token_endpoint"),
                                    "registration_endpoint": data.get("registration_endpoint")
                                }
                            else:
                                # Add registration endpoint if missing
                                if not report["discovered_config"].get("registration_endpoint"):
                                    report["discovered_config"]["registration_endpoint"] = data.get("registration_endpoint")
                        else:
                            param_data[path] = {"found": False, "status": meta_resp.status_code}
                    except Exception as e:
                        param_data[path] = {"found": False, "error": str(e)}
                
                report["well_known_probe"]["paths_checked"] = param_data
                report["well_known_probe"]["status"] = "completed"
                
            except Exception as e:
                 report["well_known_probe"]["status"] = "error"
                 report["well_known_probe"]["details"] = str(e)
                 
        return report
