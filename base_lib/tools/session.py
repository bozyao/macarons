# coding: utf-8
# __author__ = 'bozyao'

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, date

import redis


def format_date(obj):
    """json dumps时使用的输出格式（暂时先这两个，以后可以加入，如自定义的对象）
        @param obj: 需要转换的对象
        @return: 转换后的样子
    """
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')


class SessionData(dict):
    def __init__(self, session_id, hmac_key):
        self.session_id = session_id
        self.hmac_key = hmac_key


class Session(SessionData):
    def __init__(self, session_manager, request_handler):
        self.session_manager = session_manager
        self.request_handler = request_handler
        try:
            current_session = session_manager.get(request_handler)
        except InvalidSessionException:
            current_session = session_manager.get()

        for key, data in current_session.items():
            self[key] = data

        self.session_id = current_session.session_id
        self.hmac_key = current_session.hmac_key

    def save(self, raw_data):
        if not isinstance(raw_data, dict):
            return
        for key, data in raw_data.items():
            self[key] = data
        self.session_manager.set(self, self.request_handler)

    def remove(self):
        self.session_manager.remove(self)

    def get_all(self):
        return self.session_manager.get_all()


class SessionManager(object):
    def __init__(self, secret, store_options, session_timeout, m_db=None):
        self.secret = secret
        self.session_timeout = session_timeout
        self.m_db = m_db
        try:
            self.redis = redis.StrictRedis(host=store_options['redis_host'],
                                           port=store_options['redis_port'],
                                           db=store_options['redis_db'])
        except Exception as e:
            print(e)
            logging.error("Session redis connect error! %s" % e)

    def _fetch(self, session_id):
        try:
            session_data = raw_data = self.redis.get(session_id)
            # if not raw_data:
            #    session_data = raw_data = self.get_m_db_data(session_id)

            if raw_data:
                # self.redis.set(session_id, raw_data)
                self.redis.setex(session_id, self.session_timeout, raw_data)
                try:
                    session_data = json.loads(raw_data)
                except:
                    session_data = {}

            if isinstance(session_data, dict):
                return session_data
            else:
                return {}
        except IOError:
            return {}

    def get_session_id(self, request_handler, session_key="QFUSERSESSION"):

        session_id = ""
        if not request_handler.get_argument("sid", ""):
            t_session_id = request_handler.get_cookie(session_key)
            session_id = request_handler.get_cookie("sid")
            if not t_session_id and session_id and len(session_id) == 36:
                pass
            elif t_session_id:
                session_id = t_session_id
            else:
                session_id = request_handler.get_secure_cookie(session_key)
        else:
            session_id = request_handler.get_argument("sid", "")

        return session_id

    def _gen_session(self):
        session_id = self._generate_id()
        hmac_key = self._generate_hmac(session_id)

    def get(self, request_handler=None):
        if (request_handler == None):
            session_id = None
            hmac_key = ''
        else:
            session_id = self.get_session_id(request_handler)
            # hmac_key = request_handler.get_secure_cookie("verification")
            hmac_key = ''

        if not session_id:
            session_exists = False
            session_id = self._generate_id()
            # hmac_key = self._generate_hmac(session_id)
            hmac_key = ''
        else:
            session_exists = True

        # check_hmac = self._generate_hmac(session_id)
        # if hmac_key != check_hmac:
        #    raise InvalidSessionException()

        session = SessionData(session_id, hmac_key)
        if session_exists:
            session_data = self._fetch(session_id)
            for key, data in session_data.items():
                session[key] = data
        return session

    def set(self, session, request_handler=None, session_key="QFUSERSESSION"):
        request_handler.set_cookie(session_key, session.session_id)
        # request_handler.set_secure_cookie("verification", session.hmac_key)

        session_dict = dict(session.items())
        session_data = json.dumps(session_dict, default=format_date)
        # self.set_m_db_data(session.session_id, session_data)
        if 'userid' in session_dict:
            s_k = 's%s' % session_dict['userid']
            if not self.redis.sismember(s_k, session.session_id):
                c = self.redis.scard(s_k)
                while c >= 20:
                    self.redis.delete(self.redis.spop(s_k))
                    c -= 1
                self.redis.sadd(s_k, session.session_id)

        self.redis.setex(session.session_id, self.session_timeout, session_data)

    def clear(self, userid):
        s_k = 's%s' % userid
        session_set = self.redis.smembers(s_k)
        if not session_set:
            return
        for session_id in session_set:
            self.redis.delete(session_id)
        return len(session_set)

    def remove(self, session):
        # self.rm_m_db_data(session.session_id)
        if 'userid' in session:
            s_k = 's%s' % session['userid']
            self.redis.srem(s_k, session.session_id)
        self.redis.delete(session.session_id)

    def get_all(self):
        return len(self.redis.keys())

    def _generate_id(self):
        # new_id = hashlib.sha256(self.secret + str(uuid.uuid4()))
        new_id = hashlib.sha1((self.secret + str(uuid.uuid4())).encode("utf8"))
        return new_id.hexdigest()

    def _generate_hmac(self, session_id):
        return hmac.new(session_id, self.secret, hashlib.sha256).hexdigest()

    def set_m_db_data(self, k, v):
        if not self.m_db:
            return 0
        if not v:
            return 0
        # data = self.m_db.get("select * from user_session where sid = '%s'" % k)
        data = self.get_m_db_data(k)
        if data:
            flag = self.m_db.execute("update user_session set vl = '%s' where sid = '%s'" % (v, k))
        else:
            flag = self.m_db.insert("user_session", {
                "sid": k,
                "vl": v
            })
        return flag

    def get_m_db_data(self, k):
        if not self.m_db:
            return None
        sql = "select vl from user_session where sid = '%s'" % k
        data = self.m_db.get(sql)
        if data:
            data = data["vl"]
        return data

    def rm_m_db_data(self, k):
        if not self.m_db:
            return 0
        return self.m_db.execute("delete from user_session where sid='%s'" % k)


class InvalidSessionException(Exception):
    pass
