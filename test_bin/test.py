# coding: utf-8

from base_lib.app_route import route, check_session, RequestHandler, async


@route()
class TestHandler(RequestHandler):
    def post(self):
        self.ret_data(
            {"data": 'hello world'}
        )


@route("/test/(\d+)")
class TestHandler(RequestHandler):
    @async
    def get(self, n):
        import time
        time.sleep(int(n))
        self.ret_data({"sleep_time": n})


@route("/test1/(\d+)")
class Test1Handler(RequestHandler):
    def get(self, n):
        import time
        time.sleep(int(n))
        self.ret_data({"sleep_time": n})


@route()
class WorldHandler(RequestHandler):
    @check_session()
    # 必须登录，cookie中有session_id=xxxxxx，xxxx在redis中有数据userid
    def get(self):
        self.ret_data(
            {"msg": "Say 'Hello world!'"}
        )
