#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import re
import shutil
import subprocess

DOMAIN_PATH = '/etc/dovecot/domains'
MAILDIR_PATH = '~/mail'
ACCOUNTS_FILE = '.mailaccounts2'

ALIAS_FILE = '/etc/postfix/alias_maps'
ACCOUNT_FILE = '/etc/postfix/account_maps'
CATCHALL_FILE = '/etc/postfix/catchall_maps'
PASSWD_FILE = '/etc/dovecot/passwd'
DOMAIN_FILE = '/etc/postfix/domain_maps'

TMP_SUFIX = '.tmp'
OLD_SUFIX = '.old'

POSTMAP_BIN = '/usr/sbin/postmap'
DOVECOTPW_BIN = '/usr/sbin/dovecotpw'


CATCHALL_FILE_TMP = CATCHALL_FILE + TMP_SUFIX
PASSWD_FILE_TMP = PASSWD_FILE + TMP_SUFIX
DOMAIN_FILE_TMP = DOMAIN_FILE + TMP_SUFIX

CATCHALL_FILE_OLD = CATCHALL_FILE + OLD_SUFIX
PASSWD_FILE_OLD = PASSWD_FILE + OLD_SUFIX
DOMAIN_FILE_OLD = DOMAIN_FILE + OLD_SUFIX

CATCHALL_FILE_DB = CATCHALL_FILE + '.db'
DOMAIN_FILE_DB = DOMAIN_FILE + '.db'
CATCHALL_FILE_TMP_DB = CATCHALL_FILE + TMP_SUFIX + '.db'
DOMAIN_FILE_TMP_DB = DOMAIN_FILE + TMP_SUFIX + '.db'

RE_WS = re.compile('\s+')

FORBIDDEN_USERS = ('abuse', 'postmaster')

class ConfigError(Exception):
    pass

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


class UserMailConfigParser(SimpleParser):
    def __init__(self, domains):
        self.catchalls = dict() # domain: account
        self.aliases = dict() # alias: account
        self.account_pass = dict() # account: pass
        self.accounts = set()
        self.domains = domains
        self.errors = []

    def error(self, description):
        self.errors.append(self.format_error(description))

    def parse_account(self, account):
        tmp = account.split('@')
        if len(tmp) != 2:
            raise ParseError('Malformed account name')
        
        user, domain = tmp
        if user.find('-') != -1:
            raise ParseError('Username cannot contain "-" (dash) character')

        if user in FORBIDDEN_USERS:
            raise ParseError('You cannot use username "%s"' % user)

        if domain not in self.domains:
            raise ParseError('Unknown domain "%s"' % domain)

        return user, domain

    def cmd_account(self, account, password):
        user, domain = self.parse_account(account)

        if account in self.aliases:
            del self.aliases[account]

        self.accounts.add(account)
        self.account_pass[account] = password

    def cmd_alias(self, account1, account2):
        user, domain = self.parse_account(account1)

        if account1 in self.accounts:
            raise ParseError('Account "%s" already exists' % account1)
        
        alias = self.aliases.get(account2)
        if alias:
            account2 = alias
        elif account2 not in self.accounts:
            raise ParseError('Unknown account "%s"' % account2)
        
        self.aliases[account1] = account2

    def cmd_catchall(self, domain, account):
        if domain not in self.domains:
            raise ParseError('Unknown domain "%s"' % domain)

        alias = self.aliases.get(account)
        if alias:
            account = alias
        elif account not in self.accounts:
            raise ParseError('Unknown account "%s"' % account)

        self.catchalls[domain] = account


def mail_reload(context, arguments):
    errors = context['response']['errors']
    user = context['user']

    config_fp = os.path.join(user.pw_dir, ACCOUNTS_FILE)
    if not os.path.isfile(config_fp):
        errors.append('No configuration file exists')

    domains = set()

    domain_fp = os.path.join(DOMAIN_PATH, user.pw_name)
    if not os.path.isfile(domain_fp):
        errors.append('No domain file exists')
        failed = True
    else:
        f = open(domain_fp, 'r')
        num = 1
        for line in f.xreadlines():
            line = line.strip()
            if not line or line.startswith('#'): continue
            domains.add(line)
        f.close()

    if not errors:
        parser = UserMailConfigParser(domains)
        parser.parse(config_fp)
        # must use +=, or else we would have to replace errors from context
        errors += parser.errors

    if errors:
        return

    print parser.catchalls
    print parser.aliases
    print parser.account_pass
    print parser.accounts
    print parser.domains

MOD_NAME = 'mail'
MOD_COMMANDS = {
    'reload': mail_reload,
}
