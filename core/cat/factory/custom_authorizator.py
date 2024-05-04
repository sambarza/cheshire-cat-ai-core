from fastapi import (
    WebSocket,
    Request,
    HTTPException
)
class AuthorizatorNoAuth():
    def __init__(self):
        pass

    def is_allowed(self, request: Request):
        return True
    
    def is_allowed_ws(self, websocket: WebSocket):
        return True

class AuthorizatorApiKey():
    def __init__(self, api_key):
        self.api_key = api_key
    
    def is_allowed(self, request: Request):
        if request.headers.get("Authorization") != self.api_key:
            raise HTTPException(
                status_code=403,
                detail={"error": "Invalid API Key"}
            )

    def is_allowed_ws(self, websocket: WebSocket):
        if websocket.headers.get("Authorization") != self.api_key:
            raise HTTPException(
                status_code=403,
                detail={"error": "Invalid API Key"}
            )
