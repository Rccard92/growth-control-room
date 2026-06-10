from fastapi import APIRouter, Request
from starlette.routing import Route

router = APIRouter(prefix="/debug", tags=["debug"])


def _collect_routes(request: Request) -> list[dict[str, object]]:
    routes: list[dict[str, object]] = []
    for route in request.app.routes:
        if not isinstance(route, Route):
            continue
        methods = sorted(method for method in route.methods if method != "HEAD")
        routes.append(
            {
                "path": route.path,
                "methods": methods,
                "name": route.name,
            }
        )
    return sorted(routes, key=lambda item: (str(item["path"]), str(item["methods"])))


@router.get("/routes")
async def list_registered_routes(request: Request) -> dict[str, object]:
    routes = _collect_routes(request)
    projects_routes = [route for route in routes if "projects" in str(route["path"])]
    return {
        "count": len(routes),
        "routes": routes,
        "projects_routes": projects_routes,
    }
