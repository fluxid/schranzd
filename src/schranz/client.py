# -*- coding: utf-8 -*-

import json
import socket

def execute_command(module, command, arguments = None, socket_file='/var/run/schranz/schranz.sock'):
    data = dict(
        module = module,
        command = command,
        arguments = arguments or [],
    )
    jdata = json.dumps(data)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_file)
    sock.send(jdata)
    jreceived = sock.recv(8192)
    sock.close()

    received = json.loads(jreceived)
    return received
