# -*- coding: utf-8 -*-

import os
import sys

modules = dict()

def process_command(context, data):
    errors = context['response']['errors']
    module_n = data.get('module')
    command_n = data.get('command')
    arguments = data.get('arguments', [])
    if not (module_n and command_n):
        errors.append('Missing module name or command')
        return
    module = modules.get(module_n)
    if not module:
        errors.append('Unknown module: `%s`' % module_n)
        return
    command = module.get(command_n)
    if not command:
        errors.append('Unknown command: `%s`' % command_n)
        return
    if not isinstance(arguments, list):
        errors.append('Invalid arguments list')
        return
    
    command(context, arguments)


for filename in os.listdir(os.path.abspath(__path__[0])):
    if filename[-3:] == '.py' and filename != '__init__.py':
        f, e = os.path.splitext(filename)
        mod = __import__(f, globals(), locals(), [])
        try:
            modules[mod.MOD_NAME] = mod.MOD_COMMANDS
        except:
            continue
