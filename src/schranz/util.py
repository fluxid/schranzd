# -*- coding: utf-8 -*-

import grp
import pwd
import socket
import struct

SO_PEERCRED = 17

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
