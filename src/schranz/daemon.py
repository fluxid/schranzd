# -*- coding: utf-8 -*-

import json
import os

import gevent
from gevent import socket

from schranz import util
from schranz.modules import process_command

class SchranzDaemon(object):
    def __init__(self):
        self.queue = []
        self.workers = []

    def process_connection(self, conn):
        current = gevent.getcurrent()
        self.workers.append(current)

        pid, uid, gid = util.get_credentials(conn)
        user = util.get_user(uid)
        group = util.get_group(gid)

        context = dict(
            user = user,
            group = group,
            pid = pid,
        )

        print 'Connection: %s %s' % (user.pw_name, pid) 
        while True:
            jdata = conn.recv(4096)
            if not jdata:
                break

            errors = []
            response = dict(
                errors = errors,
            )
            context['response'] = response

            try:
                data = json.loads(jdata)
            except:
                data = None
            if not isinstance(data, dict):
                errors.append('Error while parsing command.')
            else:
                try:
                    process_command(context, data)
                except:
                    import traceback; traceback.print_exc()
                    errors.append('Critical error while executing command.')

            jresponse = json.dumps(response)
            conn.send(jresponse)

            if errors:
                break

        conn.close()
        
        self.workers.remove(current)

    def run(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind('schranzd.sock')
        sock.listen(1)
        try:
            while True:
                conn, addr = sock.accept()
                gevent.spawn(self.process_connection, conn)
        except:
            raise
        finally:
            try:
                gevent.joinall(self.workers, 5)
                gevent.killall(self.workers)
                os.remove('schranzd.sock')
            except:
                pass
