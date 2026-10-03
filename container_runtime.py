"""Loopback-only adapter for a single private Docker workspace.

Never expose this listener directly. The Studio account gateway authenticates
both HTTP and noVNC, and this process shares only its owner's browser profiles.
"""
import asyncio
import json
import threading
import urllib.request
import tornado.ioloop
import tornado.web
import app as publisher

PLATFORMS = {
    'shipinhao': (5006, 'https://channels.weixin.qq.com/platform/post/create'),
    'instagram': (5007, 'https://www.instagram.com/'),
    'youtube': (9222, 'https://studio.youtube.com/'),
    'douyin': (5004, 'https://creator.douyin.com/creator-micro/content/upload'),
    'xiaohongshu': (5003, 'https://creator.xiaohongshu.com/creator/post'),
    'bilibili': (5005, 'https://member.bilibili.com/platform/upload/video/frame'),
}
_opening = False


class PlatformLoginHandler(tornado.web.RequestHandler):
    async def post(self):
        global _opening
        data = json.loads(self.request.body)
        platform = data.get('platform')
        if platform not in PLATFORMS:
            raise tornado.web.HTTPError(400, 'Unknown platform')
        if _opening or publisher.is_publishing or not publisher.PUBLISH_QUEUE.empty():
            self.set_status(409)
            self.write({'error': 'Publishing is active. Wait before opening a login page.'})
            return
        if not publisher.BROWSER_CONTROL_LOCK.acquire(blocking=False):
            self.set_status(409)
            self.write({'error': 'The publisher is using the browser. Try again later.'})
            return
        _opening = True
        try:
            port, url = PLATFORMS[platform]
            browser = publisher._resolve_browser_bin()
            prefix = publisher._resolve_session_prefix(browser)
            import os
            profile = publisher._resolve_profile_dir(port, prefix)
            logs = publisher._resolve_logs_dir(prefix)
            os.makedirs(profile, exist_ok=True)
            os.makedirs(logs, exist_ok=True)
            command = publisher._build_start_command(platform, port, url, browser,
                        publisher._resolve_display(), profile, logs, prefix)
            await asyncio.to_thread(publisher._start_browser_if_needed, platform, port, command, url)
            # Activate an observed page in the selected profile, without
            # navigating away from a login challenge or opening a duplicate tab.
            def activate():
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list', timeout=3) as response:
                    pages = json.load(response)
                page = next((p for p in pages if p.get('type') == 'page'), None)
                if page:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/activate/{page["id"]}', timeout=3):
                        pass
            try:
                await asyncio.to_thread(activate)
            except Exception as exc:
                print(f'Browser opened but could not focus tab: {type(exc).__name__}')
            self.write({'opened': True, 'platform': platform})
        finally:
            _opening = False
            publisher.BROWSER_CONTROL_LOCK.release()


if __name__ == '__main__':
    publisher.restore_publish_queue()
    threading.Thread(target=publisher._publish_worker, daemon=True).start()
    app = publisher.make_app()
    app.add_handlers(r'.*', [(r'/platform-login', PlatformLoginHandler)])
    app.listen(8081, address='127.0.0.1', max_body_size=10 * 1024**3)
    tornado.ioloop.IOLoop.current().start()
