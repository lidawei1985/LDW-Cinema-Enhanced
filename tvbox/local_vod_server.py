import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

MOVIES = [
    {
        "vod_id": "sintel",
        "vod_name": "Sintel",
        "vod_pic": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Sintel_poster.jpg/480px-Sintel_poster.jpg",
        "vod_remarks": "开源电影",
        "vod_content": "Blender 基金会发布的开放电影。",
        "vod_play_from": "公开线路",
        "vod_play_url": "正片$https://media.w3.org/2010/05/sintel/trailer.mp4",
    },
    {
        "vod_id": "bunny",
        "vod_name": "Big Buck Bunny",
        "vod_pic": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/480px-Big_buck_bunny_poster_big.jpg",
        "vod_remarks": "开源电影",
        "vod_content": "Blender 基金会发布的开放动画电影。",
        "vod_play_from": "公开线路",
        "vod_play_url": "正片$https://media.w3.org/2010/05/bunny/trailer.mp4",
    },
    {
        "vod_id": "flower",
        "vod_name": "Flower",
        "vod_pic": "https://peach.blender.org/wp-content/uploads/title_anouncement.jpg",
        "vod_remarks": "公开测试",
        "vod_content": "用于验证 TVBox 点播播放链路。",
        "vod_play_from": "公开线路",
        "vod_play_url": "正片$https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
    },
]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        action = query.get("ac", [""])[0]
        ids = query.get("ids", [""])[0]
        if action in ("detail", "videolist") and ids:
            selected = [movie for movie in MOVIES if movie["vod_id"] in ids.split(",")]
            payload = {"code": 1, "list": selected}
        else:
            payload = {
                "code": 1,
                "page": 1,
                "pagecount": 1,
                "limit": 20,
                "total": len(MOVIES),
                "class": [{"type_id": "movie", "type_name": "开源电影"}],
                "list": MOVIES,
            }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)


ThreadingHTTPServer(("0.0.0.0", 18080), Handler).serve_forever()
