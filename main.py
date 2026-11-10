from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import msal
import httpx
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

app = FastAPI(title="Python BFF with Azure AD")

# --------------------------
# 1. 基础中间件配置
# --------------------------
# CORS：允许 React 前端跨域，必须允许携带凭证（Cookie）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 开发地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session：加密 Cookie 存储会话（生产环境建议替换为 Redis Session）
# Secret Key 用于签名 Cookie，生产环境请使用强随机字符串
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-in-prod"),
    session_cookie="bff_session",
    same_site="lax",  # 防御 CSRF，生产环境可设为 strict
    https_only=True if os.getenv("ENV") == "prod" else False,
)

# --------------------------
# 2. Azure AD 配置
# --------------------------
AZURE_CONFIG = {
    "client_id": os.getenv("AZURE_CLIENT_ID"),
    "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
    "tenant_id": os.getenv("AZURE_TENANT_ID"),
    "authority": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}",
    "redirect_uri": os.getenv("AZURE_REDIRECT_URI", "http://localhost:8000/auth/callback"),
    "scopes": ["email", f"api://{os.getenv('AZURE_API_CLIENT_ID')}/.default"],
    #["openid", "profile", "email", f"api://{os.getenv('AZURE_API_CLIENT_ID')}/.default"],
}

# 初始化 MSAL 客户端
msal_client = msal.ConfidentialClientApplication(
    client_id=AZURE_CONFIG["client_id"],
    client_credential=AZURE_CONFIG["client_secret"],
    authority=AZURE_CONFIG["authority"],
)

# 下游 API 地址
DOWNSTREAM_API_URL = os.getenv("DOWNSTREAM_API_URL", "https://your-downstream-api.example.com")

# --------------------------
# 3. 认证工具函数
# --------------------------
async def get_valid_access_token(request: Request) -> str:
    """从 Session 中获取有效 Access Token，自动处理过期刷新"""
    token_cache = request.session.get("token_cache")
    if not token_cache:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # 加载 Token 缓存
    msal_client.token_cache.deserialize(token_cache)
    accounts = msal_client.get_accounts()
    
    if not accounts:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session expired")
    
    # 尝试静默获取 Token（自动使用 Refresh Token 刷新）
    result = msal_client.acquire_token_silent(
        scopes=AZURE_CONFIG["scopes"],
        account=accounts[0],
    )
    
    if not result or "access_token" not in result:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Failed to refresh token")
    
    # 更新 Session 中的 Token 缓存
    request.session["token_cache"] = msal_client.token_cache.serialize()
    return result["access_token"]

# --------------------------
# 4. 认证接口
# --------------------------
@app.get("/auth/login")
async def login():
    """触发 Azure AD 登录重定向"""
    auth_url = msal_client.get_authorization_request_url(
        scopes=AZURE_CONFIG["scopes"],
        redirect_uri=AZURE_CONFIG["redirect_uri"],
    )
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, error: str = None):
    """处理 Azure AD 授权回调，换取 Token"""
    if error:
        return JSONResponse(status_code=400, content={"error": error})
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")
    
    # 用 Code 换取 Token
    result = msal_client.acquire_token_by_authorization_code(
        code=code,
        scopes=AZURE_CONFIG["scopes"],
        redirect_uri=AZURE_CONFIG["redirect_uri"],
    )
    
    if "error" in result:
        return JSONResponse(status_code=401, content=result)
    
    # 将 Token 缓存存入 Session（不会暴露给前端）
    request.session["token_cache"] = msal_client.token_cache.serialize()
    request.session["user"] = result.get("id_token_claims", {})
    
    # 登录成功后重定向回 React 前端
    return RedirectResponse("http://localhost:3000")

@app.get("/auth/logout")
async def logout(request: Request):
    """注销：清除本地会话 + 重定向到 Azure AD 注销页"""
    request.session.clear()
    logout_url = f"{AZURE_CONFIG['authority']}/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:3000"
    return RedirectResponse(logout_url)

@app.get("/auth/me")
async def get_current_user(request: Request):
    """获取当前登录用户信息"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}

# --------------------------
# 5. BFF 代理接口示例
# --------------------------
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(
    path: str,
    request: Request,
    access_token: str = Depends(get_valid_access_token)
):
    """通用代理：将 /api/* 请求转发给下游 API，并注入 Authorization Header"""
    # 构造下游请求 URL
    url = f"{DOWNSTREAM_API_URL}/{path}"
    
    # 读取前端发来的请求体和查询参数
    body = await request.body()
    query_params = dict(request.query_params)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": request.headers.get("Content-Type", "application/json"),
    }
    
    # 转发请求
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                content=body,
                params=query_params,
                headers=headers,
                timeout=30.0,
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code,
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Downstream API error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)