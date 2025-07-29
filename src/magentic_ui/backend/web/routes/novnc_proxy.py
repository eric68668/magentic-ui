import logging
from typing import Dict, Optional
from fastapi import APIRouter, Request, Response
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储浏览器实例的端口映射
browser_instances: Dict[str, Dict[str, int]] = {}


class NoVNCProxy:
    """noVNC代理转发器"""

    def __init__(self):
        self.browser_instances: Dict[str, Dict[str, int]] = {}

    def register_browser(self, session_id: str, novnc_port: int, playwright_port: int):
        """注册浏览器实例"""
        self.browser_instances[session_id] = {
            "novnc_port": novnc_port,
            "playwright_port": playwright_port,
        }
        logger.info(
            f"Registered browser for session {session_id}: novnc={novnc_port}, playwright={playwright_port}"
        )

    def get_browser_ports(self, session_id: str) -> Optional[Dict[str, int]]:
        """获取浏览器端口信息"""
        return self.browser_instances.get(session_id)

    def unregister_browser(self, session_id: str):
        """注销浏览器实例"""
        if session_id in self.browser_instances:
            del self.browser_instances[session_id]
            logger.info(f"Unregistered browser for session {session_id}")


# 全局代理实例
novnc_proxy = NoVNCProxy()


@router.get("/browser/{session_id}/vnc.html")
async def proxy_vnc_html(session_id: str, request: Request):
    """代理noVNC HTML页面"""
    browser_info = novnc_proxy.get_browser_ports(session_id)
    if not browser_info:
        return Response(status_code=404, content="Browser session not found")

    novnc_port = browser_info["novnc_port"]
    target_url = f"http://localhost:{novnc_port}/vnc.html"

    # 转发查询参数
    query_string = str(request.query_params)
    if query_string:
        target_url += f"?{query_string}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url)

            # 修改HTML内容，将相对路径改为代理路径
            content = response.text
            content = content.replace(
                f"http://localhost:{novnc_port}", f"/api/novnc/browser/{session_id}"
            )

            return Response(
                content=content,
                media_type="text/html",
                headers={"Cache-Control": "no-cache"},
            )
    except Exception as e:
        logger.error(f"Error proxying VNC HTML for session {session_id}: {e}")
        return Response(status_code=502, content="Failed to proxy VNC HTML")


@router.get("/browser/{session_id}/{path:path}")
async def proxy_vnc_static(session_id: str, path: str, request: Request):
    """代理noVNC静态资源"""
    browser_info = novnc_proxy.get_browser_ports(session_id)
    if not browser_info:
        return Response(status_code=404, content="Browser session not found")

    novnc_port = browser_info["novnc_port"]
    target_url = f"http://localhost:{novnc_port}/{path}"

    # 转发查询参数
    query_string = str(request.query_params)
    if query_string:
        target_url += f"?{query_string}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url)
            return Response(
                content=response.content,
                media_type=response.headers.get(
                    "content-type", "application/octet-stream"
                ),
                headers={
                    "Cache-Control": "no-cache",
                    **{
                        k: v
                        for k, v in response.headers.items()
                        if k.lower() not in ["content-length", "transfer-encoding"]
                    },
                },
            )
    except Exception as e:
        logger.error(
            f"Error proxying VNC static for session {session_id}, path {path}: {e}"
        )
        return Response(status_code=502, content="Failed to proxy VNC static")


@router.delete("/unregister/{session_id}")
async def unregister_browser(session_id: str):
    """注销浏览器实例"""
    try:
        novnc_proxy.unregister_browser(session_id)
        return {
            "status": "success",
            "message": f"Browser unregistered for session {session_id}",
        }
    except Exception as e:
        logger.error(f"Error unregistering browser: {e}")
        return Response(status_code=500, content="Failed to unregister browser")


@router.get("/status/{session_id}")
async def get_browser_status(session_id: str):
    """获取浏览器状态"""
    browser_info = novnc_proxy.get_browser_ports(session_id)
    if browser_info:
        return {
            "status": "active",
            "session_id": session_id,
            "novnc_port": browser_info["novnc_port"],
            "playwright_port": browser_info["playwright_port"],
            "vnc_url": f"/api/novnc/browser/{session_id}/vnc.html",
        }
    else:
        return {"status": "not_found", "session_id": session_id}
