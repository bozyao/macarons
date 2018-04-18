# coding: utf-8

import json
import redis
import time
import copy
import datetime
import types
import random
import logging

try:
    from conf.settings import BUSINESS_REDIS
    logging.info("Redis config by local......")
except ImportError:
    from base_conf.settings import BUSINESS_REDIS
    logging.info("Redis config by base......")

class BaseCache(object):
    def __init__(self, db=BUSINESS_REDIS['db'], host=BUSINESS_REDIS['host'], port=BUSINESS_REDIS['port'], kc={}):
        """
        初始化redis对象r, 初始化配置信息kc(keys_config), 例如:
        'cache_1':{
            'db':0,            #使用数据库，非必须参数，默认为参数db值
            'key':'%s_key1',   #实际存储key
            'type':'str',      #存储类型
            'timeout':86400,   #超时时间
            'postpone':0,      #读取数据时，是否顺延timeout，0=不顺延，1=顺延，非必须参数，默认为0
            'random':43200,    #写入数据时，timeout随机添加0-43200，防止批量刷新缓存后，同时失效，非必须参数，默认为0
        }
        """
        self.db = db
        self.r  = redis.StrictRedis(host=host, port=port, db=db)
        self.kc = kc 

    def get_conf(self, ckey, rkey, charset='utf-8'):
        """
        @param ckey: 配置文件的key 
        @return: 返回相应配置

        """
        try:
            if not ckey:
                return None
            tmp_kc = copy.deepcopy(self.kc)
            #不允许存在无过期时间的数据
            if ckey not in tmp_kc or 'timeout' not in tmp_kc[ckey] or 'key' not in tmp_kc[ckey]:
                return None

            #处理rkey
            if '%' in tmp_kc[ckey]['key']:
                if not rkey:
                    return None
                if isinstance(rkey, types.UnicodeType):
                    rkey = rkey.encode(charset, 'ignore')
                tmp_kc[ckey]['key'] = tmp_kc[ckey]['key'] % rkey

            #处理timeout
            if tmp_kc[ckey].get('random', 0):
                tmp_kc[ckey]['timeout'] = tmp_kc[ckey]['timeout'] + random.randint(0, tmp_kc[ckey].get('random', 0))

            #切换数据库
            if 'db' in tmp_kc[ckey] and tmp_kc[ckey]['db'] != self.db:
                self.r.select(tmp_kc[ckey]['db'])

            return tmp_kc[ckey] 
        except:
            return None

    def str2dict(self, val):
        """
        @param val: 数据字符串
        @return: 数据字典
        """ 
        try:
            return json.loads(val)
        except:
            return val

    def dict2str(self, val):
        """
        @param val: 数据字典
        @return: 数据字符串
        """ 
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, datetime.datetime):
                    val[k] = v.strftime("%Y-%m-%d %H:%M:%S")  
            return json.dumps(val)
        else:
            return val

    def set(self, ckey, value, rkey='', charset='utf-8'):
        """
        @param ckey: 配置文件key 
        @param rkey: 写入redis数据的key 
        @param value: 要写入redis的数据 
        @return: 成功与否
        """ 
        if True:
            c = self.get_conf(ckey, rkey)
        
            if not c:
                return

            k = c['key']
            t = c['type']

            #写入数据为空时，删除已有key
            if not value and self.r.exists(k):
                self.r.delete(k)
                return True

            if t == 'str':
                value = self.dict2str(value)
                self.r.set(k, value)
            elif t == 'hash':
                self.r.hmset(k, value)
            elif t == 'list':
                if isinstance(value, (types.TupleType, types.ListType)):
                    for d in value:
                        self.r.rpush(k, d)
                else: 
                    self.r.rpush(k, value)
            elif t == 'set':
                if isinstance(value, (types.TupleType, types.ListType)):
                    for d in value:
                        redis['write'].sadd(k, d)
                else:
                    redis['write'].sadd(k, value) 
            elif t == 'sortedset':
                self.r.zadd(k, value, int(time.time()))

            if self.r.exists(k):
                self.r.expire(k, c['timeout'])
            
            return True
        #except:
        #    return None

    def get(self, ckey, rkey, ext={}, charset='utf-8'):
        """
        @param ckey: 配置文件key 
        @param rkey: 写入redis数据的key 
        @return: 读取的值
        """
        if True:
            c = self.get_conf(ckey, rkey)
            if not c:
                return

            k = c['key']
            t = c['type']

            if c['postpone'] and self.r.exists(k):
                self.r.expire(k, c['timeout'])

            s = ext.get('min', 0)
            e = ext.get('max', -1)

            if t == 'str':
                return self.str2dict(self.r.get(k))
            elif t == 'hash':
                return self.r.hgetall(k)
            elif t == 'list':
                return self.r.lrange(k, s, e)
            elif t == 'set':
                return self.smembers(k)
            elif t == 'sortedset':
                return self.r.zrangebyscore(k, s, e, withscores=True)
        #except:
        #    pass
        return

    def refresh(self, ckey, value, rkey, charset='utf-8'):
        """ 重刷rkey的数据
        @param ckey: 配置文件key 
        @param rkey: 写入redis数据的key 
        @return: 成功与否 
        """
        try:
            c = self.get_conf(ckey, rkey)
            if not c:
                return

            if self.r.exists(k):
                self.r.delete(k)

            return self.set(ckey, value, rkey, charset)
        except:
            return None

if __name__ == "__main__":
    pass 
