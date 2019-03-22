# coding: utf-8

import datetime
import logging
import os
import random
import threading
import time
import types

debug = True
dbpool = {}


def timeit(func):
    def _(*args, **kwargs):
        start = time.time()
        err = ''
        try:
            retval = func(*args, **kwargs)
            return retval
        except Exception as e:
            err = str(e)
            raise
        finally:
            end = time.time()
            conn = args[0]
            dbcf = conn.param
            logging.info('name=%s|user=%s|addr=%s:%d|db=%s|time=%d|sql=%s|err=%s',
                         conn.name, dbcf.get('user', ''),
                         dbcf.get('host', ''), dbcf.get('port', 0),
                         os.path.basename(dbcf.get('db', '')),
                         int((end - start) * 1000000),
                         repr(args[1]), err)

    return _


class DBPoolBase:
    def acquire(self, name):
        pass

    def release(self, name, conn):
        pass


class DBResult:
    def __init__(self, fields, data):
        self.fields = fields
        self.data = data

    def todict(self):
        ret = []
        for item in self.data:
            ret.append(dict(zip(self.fields, item)))
        return ret

    def __iter__(self):
        for row in self.data:
            yield dict(zip(self.fields, row))

    def row(self, i, isdict=True):
        if isdict:
            return dict(zip(self.fields, self.data[i]))
        return self.data[i]

    def __getitem__(self, i):
        return dict(zip(self.fields, self.data[i]))


class DBFunc:
    def __init__(self, data):
        self.value = data


class DBConnection:
    def __init__(self, param, lasttime, status):
        self.name = None
        self.param = param
        self.conn = None
        self.status = status
        self.lasttime = lasttime
        self.pool = None

    def is_available(self):
        if self.status == 0:
            return True
        return False

    def useit(self):
        self.status = 1
        self.lasttime = time.time()

    def releaseit(self):
        self.status = 0

    def connect(self):
        pass

    def close(self):
        pass

    def alive(self):
        pass

    def cursor(self):
        return self.conn.cursor()
    
    @timeit
    def execute(self, sql, param=None):
        logging.debug(sql)
        cur = self.conn.cursor()
        try:
            if param:
                cur.execute(sql, param)
            else:
                cur.execute(sql)
        except Exception, e:
            raise e
            # logging.warning(e)
            self.connect()
            if param:
                cur.execute(sql, param)
            else:
                cur.execute(sql)
        ret = cur.fetchall()
        cur.close()
        return ret

    @timeit
    def executemany(self, sql, param):
        cur = self.conn.cursor()
        try:
            ret = cur.executemany(sql, param)
        except:
            self.connect()
            ret = cur.executemany(sql, param)
        cur.close()
        return ret

    @timeit
    def query(self, sql, param=None, isdict=True):
        '''sql查询，返回查询结果'''
        cur = self.conn.cursor()
        try:
            if not param:
                cur.execute(sql)
            else:
                cur.execute(sql, param)
        except:
            self.connect()
            if not param:
                cur.execute(sql)
            else:
                cur.execute(sql, param)
        res = cur.fetchall()
        cur.close()
        # logging.info('desc:', cur.description)
        if res and isdict:
            ret = []
            xkeys = [i[0] for i in cur.description]
            for item in res:
                ret.append(dict(zip(xkeys, item)))
        else:
            ret = res
        return ret

    @timeit
    def get(self, sql, param=None, isdict=True):
        '''sql查询，只返回一条'''
        cur = self.conn.cursor()
        try:
            if not param:
                cur.execute(sql)
            else:
                cur.execute(sql, param)
        except:
            self.connect()
            if not param:
                cur.execute(sql)
            else:
                cur.execute(sql, param)
        res = cur.fetchone()
        cur.close()
        if res and isdict:
            xkeys = [i[0] for i in cur.description]
            return dict(zip(xkeys, res))
        else:
            return res

    def value2sql(self, v, charset='utf-8'):
        tv = type(v)
        if tv in [types.StringType, types.UnicodeType]:
            if tv == types.UnicodeType:
                v = v.encode(charset)
            if v.startswith(('now()', 'md5(')):
                return v
            return "'%s'" % self.escape(v)
        elif isinstance(v, datetime.datetime):
            return "'%s'" % str(v)
        elif isinstance(v, DBFunc):
            return v.value
        else:
            if v is None:
                return 'NULL'
            return str(v)

    def dict2sql(self, d, sp=','):
        """字典可以是 {name:value} 形式，也可以是 {name:(operator, value)}"""
        x = []
        for k, v in d.items():
            if isinstance(v, types.TupleType):
                x.append('%s' % self.exp2sql(k, v[0], v[1]))
            else:
                x.append('`%s`=%s' % (k.strip(' `').replace('.', '`.`'), self.value2sql(v)))
        return sp.join(x)

    def exp2sql(self, key, op, value):
        item = '(`%s` %s ' % (key.strip('`').replace('.', '`.`'), op.strip())
        if op in ['in', 'not in']:
            item += '(%s))' % ','.join([self.value2sql(x) for x in value])
        elif op == 'between':
            item += ' %s and %s)' % (self.value2sql(value[0]), self.value2sql(value[1]))
        else:
            item += self.value2sql(value) + ')'
        return item

    def dict2insert(self, d):
        keys = d.keys()
        vals = []
        for k in keys:
            vals.append('%s' % self.value2sql(d[k]))
        new_keys = ['`' + k.strip('`') + '`' for k in keys]
        return ','.join(new_keys), ','.join(vals)

    def insert(self, table, values):
        # sql = "insert into %s set %s" % (table, self.dict2sql(values))
        keys, vals = self.dict2insert(values)
        sql = "insert into %s(%s) values (%s)" % (table, keys, vals)
        ret = self.execute(sql)
        if ret:
            ret = self.last_insert_id()
        return ret

    def insert_ignore(self, table, values):
        keys, vals = self.dict2insert(values)
        sql = "insert ignore into %s(%s) values (%s)" % (table, keys, vals)
        ret = self.execute(sql)
        if ret:
            ret = self.last_insert_id()
        return ret

    def update(self, table, values, where=None):
        sql = "update %s set %s" % (table, self.dict2sql(values))
        if where:
            sql += " where %s" % self.dict2sql(where, ' and ')
        return self.execute(sql)

    def delete(self, table, where):
        sql = "delete from %s" % table
        if where:
            sql += " where %s" % self.dict2sql(where, ' and ')
        return self.execute(sql)

    def select(self, table, where=None, fields='*', other=None, isdict=True):
        sql = "select %s from %s" % (fields, table)
        if where:
            sql += " where %s" % self.dict2sql(where, ' and ')
        if other:
            sql += ' ' + other
        return self.query(sql, None, isdict=isdict)

    def select_one(self, table, where=None, fields='*', other=None, isdict=True):
        sql = "select %s from %s" % (fields, table)
        if where:
            sql += " where %s" % self.dict2sql(where, ' and ')
        if other:
            sql += ' ' + other
        return self.get(sql, None, isdict=isdict)

    def get_page_data(self, table, where=None, fields='*', other=None, isdict=True, page_num=1, page_count=20):
        """根据条件进行分页查询

        get_page_data

        return all_count, page_num, data
            all_count: 所有数据条目数
            page_num: 当前返回数据的页码
            data: 页面数据内容
        """

        page_num = int(page_num)
        page_count = int(page_count)

        count_data = self.select_one(table, where, "count(*) as count", other, isdict=isdict)
        if count_data and count_data['count']:
            all_count = count_data["count"]
        else:
            all_count = 0
        if all_count == 0:
            return 0, page_num, []

       

        offset = page_num * page_count - page_count
        if offset > all_count:
            data = []
        else:
            other += " limit %d offset %d" % (page_count, offset)
            data = self.select(table, where, fields, other, isdict=isdict)

        return all_count, page_num, data

    def last_insert_id(self):
        pass

    def start(self):  # start transaction
        pass

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def escape(self, s):
        return s


def with_mysql_reconnect(func):
    def _(self, *args, **argitems):
        try:
            import MySQLdb
            mysqllib = MySQLdb
        except:
            logging.info("MySQLdb load error! Load pymysql...")
            import pymysql
            mysqllib = pymysql

        trycount = 3
        while True:
            try:
                x = func(self, *args, **argitems)
            except mysqllib.OperationalError as e:
                # logging.err('mysql error:', e)
                if e[0] >= 2000:  # client error
                    # logging.err('reconnect ...')
                    self.conn.close()
                    self.connect()

                    trycount -= 1
                    if trycount > 0:
                        continue
                raise
            else:
                return x

    return _


def with_pg_reconnect(func):
    def _(self, *args, **argitems):
        import psycopg2

        trycount = 3
        while True:
            try:
                x = func(self, *args, **argitems)
            except psycopg2.OperationalError as e:
                # logging.err('mysql error:', e)
                if e[0] >= 2000:  # client error
                    # logging.err('reconnect ...')
                    self.conn.close()
                    self.connect()

                    trycount -= 1
                    if trycount > 0:
                        continue
                raise
            else:
                return x

    return _


class PGConnection(DBConnection):
    name = "pg"

    def __init__(self, param, lasttime, status):
        DBConnection.__init__(self, param, lasttime, status)

        self.connect()

    def useit(self):
        self.status = 1
        self.lasttime = time.time()

    def releaseit(self):
        self.status = 0

    def connect(self):
        engine = self.param['engine']
        if engine == 'pg':
            import psycopg2

            self.conn = psycopg2.connect(host=self.param['host'],
                                         port=self.param['port'],
                                         user=self.param['user'],
                                         password=self.param['passwd'],
                                         database=self.param['db']
                                         )
            self.conn.autocommit = 1
        else:
            raise ValueError('engine error:' + engine)
            # logging.note('mysql connected', self.conn)

    def close(self):
        self.conn.close()
        self.conn = None

    @with_pg_reconnect
    def alive(self):
        if self.is_available():
            cur = self.conn.cursor()
            cur.query("show tables;")
            cur.close()
            self.conn.ping()

    @with_pg_reconnect
    def execute(self, sql, param=None):
        return DBConnection.execute(self, sql, param)

    @with_pg_reconnect
    def executemany(self, sql, param):
        return DBConnection.executemany(self, sql, param)

    @with_pg_reconnect
    def query(self, sql, param=None, isdict=True):
        return DBConnection.query(self, sql, param, isdict)

    @with_pg_reconnect
    def get(self, sql, param=None, isdict=True):
        return DBConnection.get(self, sql, param, isdict)

    def escape(self, s, enc='utf-8'):
        if type(s) == types.UnicodeType:
            s = s.encode(enc)
        import psycopg2

        ns = psycopg2._param_escape(s)
        return unicode(ns, enc)

    def last_insert_id(self):
        ret = self.query('select last_insert_id()', isdict=False)
        return ret[0][0]

    def start(self):
        sql = "start transaction"
        return self.execute(sql)

    def insert(self, table, values):
        # sql = "insert into %s set %s" % (table, self.dict2sql(values))
        ret = 0
        try:
            keys, vals = self.dict2insert(values)
            sql = "insert into %s(%s) values (%s) RETURNING id" % (table, keys, vals)
            data = self.query(sql)
            if data:
                ret = data[0].get('id')
        except Exception as e:
            logging.error(e)
        return ret

    def insert_ignore(self, table, values):
        return self.insert(table, values)


class MySQLConnection(DBConnection):
    name = "mysql"

    def __init__(self, param, lasttime, status):
        DBConnection.__init__(self, param, lasttime, status)

        self.connect()

    def useit(self):
        self.status = 1
        self.lasttime = time.time()

    def releaseit(self):
        self.status = 0

    def connect(self):
        engine = self.param['engine']
        if engine == 'mysql':

            try:
                import MySQLdb
                mysqllib = MySQLdb
            except:
                logging.info("MySQLdb load error! Load pymysql...")
                import pymysql
                mysqllib = pymysql

            self.conn = mysqllib.connect(host=self.param['host'],
                                         port=self.param['port'],
                                         user=self.param['user'],
                                         passwd=self.param['passwd'],
                                         db=self.param['db'],
                                         charset=self.param['charset'],
                                         connect_timeout=self.param.get('timeout', 20),
                                         )

            self.conn.autocommit(1)

            # if self.param.get('autocommit',None):
            #    logging.note('set autocommit')
            #    self.conn.autocommit(1)
            # initsqls = self.param.get('init_command')
            # if initsqls:
            #    logging.note('init sqls:', initsqls)
            #    cur = self.conn.cursor()
            #    cur.execute(initsqls)
            #    cur.close()
        else:
            raise ValueError('engine error:' + engine)
            # logging.note('mysql connected', self.conn)

    def close(self):
        self.conn.close()
        self.conn = None

    @with_mysql_reconnect
    def alive(self):
        if self.is_available():
            cur = self.conn.cursor()
            cur.execute("show tables;")
            cur.close()
            self.conn.ping()

    @with_mysql_reconnect
    def execute(self, sql, param=None):
        return DBConnection.execute(self, sql, param)

    @with_mysql_reconnect
    def executemany(self, sql, param):
        return DBConnection.executemany(self, sql, param)

    @with_mysql_reconnect
    def query(self, sql, param=None, isdict=True):
        return DBConnection.query(self, sql, param, isdict)

    @with_mysql_reconnect
    def get(self, sql, param=None, isdict=True):
        return DBConnection.get(self, sql, param, isdict)

    def escape(self, s, enc='utf-8'):
        if type(s) == types.UnicodeType:
            s = s.encode(enc)
        ns = self.conn.escape_string(s)
        return unicode(ns, enc)

    def last_insert_id(self):
        ret = self.query('select last_insert_id()', isdict=False)
        return ret[0][0]

    def start(self):
        sql = "start transaction"
        return self.execute(sql)


class SQLiteConnection(DBConnection):
    name = "sqlite"

    def __init__(self, param, lasttime, status):
        DBConnection.__init__(self, param, lasttime, status)

    def connect(self):
        engine = self.param['engine']
        if engine == 'sqlite':
            import sqlite3

            self.conn = sqlite3.connect(self.param['db'], isolation_level=None)
        else:
            raise ValueError('engine error:' + engine)

    def useit(self):
        DBConnection.useit(self)
        if not self.conn:
            self.connect()

    def releaseit(self):
        DBConnection.releaseit(self)
        self.conn.close()
        self.conn = None

    def escape(self, s, enc='utf-8'):
        s = s.replace("'", "\\'")
        s = s.replace('"', '\\"')
        return s

    def last_insert_id(self):
        ret = self.query('select last_insert_rowid()', isdict=False)
        return ret[0][0]

    def start(self):
        sql = "BEGIN"
        return self.conn.execute(sql)


class DBPool(DBPoolBase):
    def __init__(self, dbcf):
        # one item: [conn, last_get_time, stauts]
        self.dbconn_idle = []
        self.dbconn_using = []

        self.dbcf = dbcf
        self.max_conn = 20
        self.min_conn = 1

        if 'conn' in self.dbcf:
            self.max_conn = self.dbcf['conn']

        self.connection_class = {}
        x = globals()
        for v in x.values():
            try:
                class_type = types.ClassType
            except:
                class_type = type
            if type(v) == class_type and v != DBConnection and issubclass(v, DBConnection):
                self.connection_class[v.name] = v

        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)

        self.open(self.min_conn)

    def synchronize(func):
        def _(self, *args, **argitems):
            self.lock.acquire()
            x = None
            try:
                x = func(self, *args, **argitems)
            finally:
                self.lock.release()
            return x

        return _

    def open(self, n=1):
        param = self.dbcf
        newconns = []
        for i in range(0, n):
            try:
                myconn = self.connection_class[param['engine']](param, time.time(), 0)
                newconns.append(myconn)
            except Exception as e:
                logging.info(e)
                logging.error("%s connection error!" % param)
        self.dbconn_idle += newconns

    def clear_timeout(self):
        # logging.info('try clear timeout conn ...')
        now = time.time()
        dels = []
        allconn = len(self.dbconn_idle) + len(self.dbconn_using)
        for c in self.dbconn_idle:
            if allconn == 1:
                break
            if now - c.lasttime > 10:
                dels.append(c)
                allconn -= 1

        logging.warn('close timeout db conn:%d', len(dels))
        for c in dels:
            c.close()
            self.dbconn_idle.remove(c)

    @synchronize
    def acquire(self, timeout=None):
        try_count = 10
        while len(self.dbconn_idle) == 0:
            try_count -= 1
            if not try_count:
                break
            if len(self.dbconn_idle) + len(self.dbconn_using) < self.max_conn:
                self.open()
                continue
            self.cond.wait(timeout)

        if not self.dbconn_idle:
            return None

        conn = self.dbconn_idle.pop(0)
        conn.useit()
        self.dbconn_using.append(conn)

        if random.randint(0, 100) > 80:
            self.clear_timeout()

        return conn

    @synchronize
    def release(self, conn):
        self.dbconn_using.remove(conn)
        conn.releaseit()
        self.dbconn_idle.insert(0, conn)
        self.cond.notify()

    @synchronize
    def alive(self):
        for conn in self.dbconn_idle:
            conn.alive()

    def size(self):
        return len(self.dbconn_idle), len(self.dbconn_using)


class DBConnProxy:
    def __init__(self, master_conn, slave_conn):
        # self.name   = ''
        self.master = master_conn
        self.slave = slave_conn

        self._modify_methods = set(
            ['execute', 'executemany', 'last_insert_id', 'insert', 'update', 'delete', 'insert_list'])
        self._master_methods = {
            'selectw_one': 'select_one',
            'selectw': 'select',
            'queryw': 'query',
            'getw': 'get',
        }

    def __getattr__(self, name):
        if name in self._modify_methods:
            return getattr(self.master, name)
        elif name in self._master_methods:
            return getattr(self.master, self._master_methods[name])
        else:
            return getattr(self.slave, name)


class RWDBPool:
    def __init__(self, dbcf):
        self.dbcf = dbcf
        self.name = ''
        self.policy = dbcf.get('policy', 'round_robin')
        self.master = DBPool(dbcf.get('master', None))
        self.slaves = []

        self._slave_current = -1

        for x in dbcf.get('slave', []):
            self.slaves.append(DBPool(x))

    def get_slave(self):
        if self.policy == 'round_robin':
            size = len(self.slaves)
            self._slave_current = (self._slave_current + 1) % size
            return self.slaves[self._slave_current]
        else:
            raise ValueError('policy not support')

    def get_master(self):
        return self.master

    def acquire(self, timeout=None):
        # logging.debug('rwdbpool acquire')
        master_conn = None
        slave_conn = None

        try:
            master_conn = self.master.acquire(timeout)
            slave_conn = self.get_slave().acquire(timeout)
            return DBConnProxy(master_conn, slave_conn)
        except:
            if master_conn:
                master_conn.pool.release(master_conn)
            if slave_conn:
                slave_conn.pool.release(slave_conn)
            raise

    def release(self, conn):
        # logging.debug('rwdbpool release')
        conn.master.pool.release(conn.master)
        conn.slave.pool.release(conn.slave)

    def size(self):
        ret = {'master': self.master.size(), 'slave': []}
        for x in self.slaves:
            key = '%s@%s:%d' % (x.dbcf['user'], x.dbcf['host'], x.dbcf['port'])
            ret['slave'].append((key, x.size()))
        return ret


def checkalive(name=None):
    global dbpool
    while True:
        if name is None:
            checknames = dbpool.keys()
        else:
            checknames = [name]
        for k in checknames:
            pool = dbpool[k]
            pool.alive()
        time.sleep(300)


def install(cf, force=False):
    global dbpool
    if dbpool and not force:
        return dbpool
    dbpool = {}
    for name, item in cf.items():
        # item = cf[name]
        dbp = None
        if 'master' in item:
            dbp = RWDBPool(item)
        else:
            dbp = DBPool(item)
        dbpool[name] = dbp
    return dbpool


def acquire(name, timeout=None):
    global dbpool
    # logging.info("acquire:", name)
    pool = dbpool.get(name, None)
    x = None
    if pool:
        x = pool.acquire(timeout)
        if x:
            x.name = name
    return x


def release(conn):
    global dbpool
    # logging.info("release:", name)
    if not conn:
        return None
    pool = dbpool[conn.name]
    return pool.release(conn)


def execute(db, sql, param=None):
    return db.execute(sql, param)


def executemany(db, sql, param):
    return db.executemany(sql, param)


def query(db, sql, param=None, isdict=True):
    return db.query(sql, param, isdict)


def with_database(name, errfunc=None, errstr=''):
    def f(func):
        def _(self, *args, **argitems):
            self.db = acquire(name)
            x = None
            try:
                x = func(self, *args, **argitems)
            except:
                if errfunc:
                    return getattr(self, errfunc)(error=errstr)
                else:
                    raise
            finally:
                release(self.db)
                self.db = None
            return x

        return _

    return f


def with_database_class(name):
    def _(cls):
        try:
            cls.db = acquire(name)
        except:
            cls.db = None
        finally:
            release(cls.db)
        return cls

    return _
