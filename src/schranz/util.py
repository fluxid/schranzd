# -*- coding: utf-8 -*-

import grp
import pwd
import re
import socket
import struct

SO_PEERCRED = 17

RE_WS = re.compile('\s+')

# User and groups convenience functions

def get_user(uid = None, name = None):
    if not (bool(uid) ^ bool(name)):
        raise Exception('You must give only one of user id or name')
    if uid:
        return pwd.getpwuid(uid)
    return pwd.getpwnam(name)

def get_group(gid = None, name = None):
    if not (bool(gid) ^ bool(name)):
        raise Exception('You must give only one of group id or name')
    if gid:
        return grp.getgrgid(gid)
    return grp.getgrnam(name)

def get_group_users(group = None, gid = None, name = None):
    group = group or get_group(gid, name)

    return [
        user
        for user in pwd.getpwall()
        if user.pw_gid == group.gr_gid or user.pw_name in group.gr_mem
    ]

def get_user_groups(user = None, uid = None, name = None):
    user = user or get_user(uid, name)

    return [
        group
        for group in grp.getgrall()
        if user.pw_gid == group.gr_gid or user.pw_name in group.gr_mem
    ]

def get_credentials(sock):
    options = sock.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, struct.calcsize('3i'))
    return struct.unpack('3i', options)

class ParseError(Exception):
    pass

class SimpleParser(object):
    def parse(self, f):
        fp = open(f, 'r')
        n = 0
        self._f = f
        self._n = n
        for line in fp.xreadlines():
            n += 1
            line = line.strip()
            if not line or line[0] in ('#', ';'):
                continue
            params = RE_WS.split(line)
            command = params.pop(0)
            command = command.lower()
            to_call = getattr(self, 'cmd_'+command, None)
            self._n = n
            if to_call:
                try:
                    to_call(*params)
                except ParseError, e:
                    self.error(e)
            else:
                self.error('Unknown statement %s' % command)

        del self._f
        del self._n

    def error(self, description):
        raise NotImplementedError

    def format_error(self, description):
        if hasattr(self, '_f'):
            return 'In file %s at line %d: %s' % (self._f, self._n, description)
        return description
