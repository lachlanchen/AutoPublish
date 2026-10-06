"""Observe an existing upload without logging cookies, signed URLs or payloads."""
import argparse
import json
import re
import time
from urllib.parse import urlsplit
from urllib.request import urlopen

import websocket


def public_response(value):
    result = {}
    if not isinstance(value, dict):
        return result
    for key, item in value.items():
        if key.lower() in {"code", "status", "statuscode", "status_code", "errorcode", "message", "msg", "error"}:
            if isinstance(item, (str, int, bool)):
                result[key] = re.sub(r"https?://\S+", "[url]", item)[:240] if isinstance(item, str) else item
        if isinstance(item, dict) and key.lower() in {"responsemetadata", "base_resp", "error", "result", "data"}:
            nested = public_response(item)
            if nested:
                result[key] = nested
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5004)
    parser.add_argument("--seconds", type=int, default=600)
    args = parser.parse_args()
    with urlopen(f"http://127.0.0.1:{args.port}/json/list", timeout=10) as response:
        pages = json.load(response)
    page = next(p for p in pages if p.get("type") == "page" and urlsplit(p.get("url", "")).hostname == "creator.douyin.com")
    connection = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=2, suppress_origin=True)
    connection.send(json.dumps({"id": 1, "method": "Network.enable"}))
    requests, pending = {}, {}
    sequence = 1
    deadline = time.monotonic() + args.seconds
    try:
        while time.monotonic() < deadline:
            try:
                event = json.loads(connection.recv())
            except websocket.WebSocketTimeoutException:
                continue
            params = event.get("params", {})
            request_id = params.get("requestId")
            method = event.get("method")
            if method == "Network.requestWillBeSent":
                request = params["request"]
                host = urlsplit(request["url"]).hostname or ""
                if "tos-" in host or "vod" in host or host == "creator.douyin.com":
                    requests[request_id] = {"host": host, "method": request.get("method"), "started": time.monotonic()}
            elif request_id in requests and method == "Network.responseReceived":
                requests[request_id]["http_status"] = params["response"]["status"]
            elif request_id in requests and method in {"Network.loadingFailed", "Network.loadingFinished"}:
                info = requests.pop(request_id)
                info["seconds"] = round(time.monotonic() - info.pop("started"), 2)
                if method == "Network.loadingFailed":
                    info.update(error=params.get("errorText"), canceled=params.get("canceled", False))
                    print(json.dumps(info), flush=True)
                else:
                    sequence += 1
                    pending[sequence] = info
                    connection.send(json.dumps({"id": sequence, "method": "Network.getResponseBody", "params": {"requestId": request_id}}))
            elif event.get("id") in pending:
                info = pending.pop(event["id"])
                response = event.get("result", {})
                try:
                    info["response"] = public_response(json.loads(response.get("body", ""))) if not response.get("base64Encoded") else {}
                except ValueError:
                    info["response"] = {}
                print(json.dumps(info, ensure_ascii=False), flush=True)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
