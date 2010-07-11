#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import subprocess

from schranz.util import SimpleParser, ParseError

MAILDIR_PATH = '~/schranz/mail'
CONFIG_FILE = 'schranz/mailaccounts'

BASE_PATH = '/var/lib/schranz/mail/'
CONFIG_CACHE_PATH = BASE_PATH + 'cache/'
DOMAIN_PATH = BASE_PATH + 'domains/'

ACCOUNT_FILE = 'account_maps'
ALIAS_FILE = 'alias_maps'
CATCHALL_FILE = 'catchall_maps'
DOMAIN_FILE = 'domain_maps'
PASSWD_FILE = 'passwd'

DEFAULT_ABUSE = 'root'
DEFAULT_POSTMASTER = 'root'
FORBIDDEN_USERS = ('abuse', 'postmaster')

DOVECOTPW_BIN = '/usr/sbin/dovecotpw'


class MailConfigParser(SimpleParser):
    def __init__(self, domains):
        super(MailConfigParser, self).__init__()
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
            raise ParseError('Malformed account name.')
        
        user, domain = tmp
        if user.find('-') != -1:
            raise ParseError('Username cannot contain "-" (dash) character.')

        if user in FORBIDDEN_USERS:
            raise ParseError('You cannot use username "%s".' % user)

        if domain not in self.domains:
            raise ParseError('Unknown domain "%s".' % domain)

    def cmd_account(self, account, password):
        self.parse_account(account)

        if account in self.aliases:
            del self.aliases[account]

        self.accounts.add(account)
        self.account_pass[account] = password

    def cmd_alias(self, account1, account2):
        self.parse_account(account1)

        if account1 in self.accounts:
            raise ParseError('Account "%s" already exists.' % account1)
        
        alias = self.aliases.get(account2)
        if alias:
            account2 = alias
        elif account2 not in self.accounts:
            raise ParseError('Unknown account "%s".' % account2)
        
        self.aliases[account1] = account2

    def cmd_catchall(self, domain, account):
        if domain not in self.domains:
            raise ParseError('Unknown domain "%s".' % domain)

        alias = self.aliases.get(account)
        if alias:
            account = alias
        elif account not in self.accounts:
            raise ParseError('Unknown account "%s".' % account)

        self.catchalls[domain] = account


def mail_reload(context, arguments):
    errors = context['response']['errors']
    user = context['user']

    domains = set()

    domain_fp = os.path.join(DOMAIN_PATH, user.pw_name)
    if not os.path.isfile(domain_fp):
        errors.append('Domain file for your user does not exist.')
    else:
        f = open(domain_fp, 'r')
        for line in f.xreadlines():
            line = line.strip()
            if not line or line[0] in ('#', ';'):
                continue
            domains.add(line)
        f.close()

    if not errors:
        parser = MailConfigParser(domains)
        try:
            parser.parse(os.path.join(user.pw_dir, CONFIG_FILE))
            errors += parser.errors
        except EnvironmentError, e:
            errors.append('Error when parsing configuration: %s.' % os.strerror(e.errno))

    if not errors:
        passwords = dict()
        for key, value in parser.account_pass.iteritems():
            try:
                p = subprocess.Popen([DOVECOTPW_BIN, '-p', value], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
            except:
                errors.append('Error when hashing password for account "%s".' % key)
                continue
            
            pstdout, _ = p.communicate()
            value = pstdout.strip()
            passwords[key] = value

    if not errors:
        gen_config(
            user,
            domains,
            parser.accounts,
            parser.aliases,
            parser.catchalls,
            passwords,
        )

def gen_config(user, domains, accounts, aliases, catchalls, passwords):
    udir = os.path.join(CONFIG_CACHE_PATH, user.pw_name)
    if not os.path.exists(udir):
        os.makedirs(udir)

    account_fp = os.path.join(udir, ACCOUNT_FILE)
    f = open(account_fp, 'w')
    for value in accounts:
        f.write('%s %s\n' % (value, value))
    f.close()

    alias_fp = os.path.join(udir, ALIAS_FILE)
    f = open(alias_fp, 'w')
    for value in domains:
        f.write('abuse@%s %s\n' % (value, DEFAULT_ABUSE))
        f.write('postmaster@%s %s\n' % (value, DEFAULT_POSTMASTER))
    for key, value in aliases.iteritems():
        f.write('%s %s\n' % (key, value))
    f.close()

    catchall_fp = os.path.join(udir, CATCHALL_FILE)
    f = open(catchall_fp, 'w')
    for key, value in catchalls.iteritems():
        f.write('@%s %s\n' % (key, value))
    f.close()

    domain_fp = os.path.join(udir, DOMAIN_FILE)
    f = open(domain_fp, 'w')
    for value in domains:
        f.write('%s %s\n' % (value, value))
    f.close()

    passwd_fp = os.path.join(udir, PASSWD_FILE)
    f = open(passwd_fp, 'w')
    for value in accounts:
        f.write('%s:%s:%d:%d::%s::userdb_mail=maildir:%s\n' % (
            value,
            passwords[value],
            user.pw_uid,
            user.pw_gid,
            user.pw_dir,
            os.path.join(MAILDIR_PATH, value.replace('@', '.'))
        ))
    f.close()

MOD_NAME = 'mail'
MOD_COMMANDS = {
    'reload': mail_reload,
}
