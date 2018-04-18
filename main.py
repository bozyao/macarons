# coding: utf-8
import importlib
import logging
import os
import socket
import sys
import time

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from logging.handlers import TimedRotatingFileHandler, WatchedFileHandler

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base_lib.app_route import Application, URL_PREFIX

socket.setdefaulttimeout(10)
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

try:
    print("Load local setting...")
    new_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if new_path not in sys.path:
        sys.path.append(new_path)

    from conf.settings import settings, LOAD_MODULE, REJECT_MODULE, LOGFILE
except ImportError as e:
    print(e)
    print("Load local setting error, load base settings...")

    from base_conf.settings import settings, LOAD_MODULE, REJECT_MODULE, LOGFILE


class MyHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='MIDNIGHT', interval=1, backup_count=10, encoding=None, delay=False, utc=False):
        self.delay = delay
        self.bfn = filename
        when = when.upper()
        if when == 'M':
            self.suffix = "%Y-%m-%d_%H-%M"
        elif when == 'H':
            self.suffix = "%Y-%m-%d_%H"
        elif when == 'D' or when == 'MIDNIGHT':
            self.suffix = "%Y-%m-%d"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % when)
        self.cfn = self.get_cfn()
        TimedRotatingFileHandler.__init__(self, filename, when=when, interval=interval, backupCount=backup_count,
                                          encoding=encoding, delay=delay, utc=utc)

    def get_cfn(self):
        return self.bfn + "." + time.strftime(self.suffix, time.localtime())

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        cur_time = int(time.time())
        dst_now = time.localtime(cur_time)[-1]
        self.cfn = self.get_cfn()
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        new_rollover_at = self.computeRollover(cur_time)
        while new_rollover_at <= cur_time:
            new_rollover_at = new_rollover_at + self.interval
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:
                    addend = -3600
                else:
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at

    def _open(self):
        self.cfn = self.get_cfn()
        if self.encoding is None:
            stream = open(self.cfn, self.mode)
        else:
            import codecs
            stream = codecs.open(self.current_file_name, self.mode, self.encoding)
        if os.path.exists(self.bfn):
            try:
                os.remove(self.bfn)
            except OSError:
                pass
        try:
            os.symlink(self.cfn, self.bfn)
        except OSError:
            pass
        return stream


def current_path():
    path = os.path.realpath(sys.path[0])
    if os.path.isfile(path):
        path = os.path.dirname(path)
        return os.path.abspath(path)
    else:
        import inspect
        caller_file = inspect.stack()[1][1]
        return os.path.abspath(os.path.dirname(caller_file))


# 加载所有handler模块
def load_module(app, path):
    logging.info("Load module path:%s" % path)
    all_py = scan_dir(path)
    # 循环获取所有py文件
    for file_name in all_py:
        i = file_name.replace(path, "")
        mn = i[1:-3].replace("/", ".").replace("\\", ".")
        # print file_name, i, mn, current_path(), __file__
        m = importlib.import_module(mn)

        # 获取有效的Handler类，方法名称
        # 此处如果类名不是Handler结尾，会对自动生成url规则产生影响，暂限定
        hd = [j for j in dir(m) if j[-7:] == "Handler" and j != 'RequestHandler' and j != 'Handler']
        if hd:
            if ((LOAD_MODULE and i in LOAD_MODULE) or not LOAD_MODULE) and i not in REJECT_MODULE:
                logging.info("Load handler file: %s" % file_name)
                app.load_handler_module(m)
            else:
                logging.info("Miss handler file: %s" % file_name)
    return app


# 扫描目录，得到所有py文件
def scan_dir(path, hfs=[]):
    fds = os.listdir(path)
    for i in fds:
        i = os.path.join(path, i)
        if i[-3:] == ".py":
            hfs.append(i)
        elif os.path.isdir(i):
            hfs = scan_dir(i, hfs)
    return hfs


def config_logger(options):
    import logging
    if options is None:
        from tornado.options import options

    if options.logging is None or options.logging.lower() == 'none':
        return

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, options.logging.upper()))
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d %(levelname)1.1s %(process)5d:%(threadName)-7.7s '
            '%(module)10.10s:%(lineno)04d $$%(message)s',
        datefmt='%y%m%d %H:%M:%S'
    )
    if options.log_file_prefix:
        print("Set logging config with file at %s" % options.log_file_prefix)
        channel = MyHandler(filename=options.log_file_prefix)
        if logger.handlers:
            del logger.handlers[:]
        logger.addHandler(channel)

    if options.log_to_stderr or (options.log_to_stderr is None and not logger.handlers):
        print("Set logging config with stdout.")
        channel = logging.StreamHandler()
        logger.addHandler(channel)

    if logger.handlers:
            for l in logger.handlers:
                l.setFormatter(formatter)


def run(path="", port=8800, url_prefix=URL_PREFIX, use_session=True, debug=False):
    import base_lib.app_route
    base_lib.app_route.URL_PREFIX = url_prefix
    define("port", default=port, help="run on the given port", type=int)
    if debug:
        settings["debug"] = True
    application = Application(None, **settings)
    tornado.options.parse_command_line(final=True)

    if LOGFILE and not options.log_file_prefix:
        options.log_file_prefix = LOGFILE
    config_logger(options)

    if not path:
        path = current_path()
    load_module(application, path)

    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    from base_lib.tools import session
    from base_lib.dbpool import acquire

    if use_session:
        sessiion_db = settings.get("session_db", "")
        application.session_manager = session.SessionManager(
            settings["session_secret"],
            settings["store_options"],
            settings["session_timeout"],
            m_db=acquire(sessiion_db)
        )
    application.use_session = use_session
    http_server.listen(options.port)
    logging.info('Server start , port: %s' % options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    run()