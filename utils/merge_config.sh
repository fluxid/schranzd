#!/bin/sh

BASE_PATH="/var/lib/schranz/mail/"
CONFIG_CACHE_PATH="${BASE_PATH}cache/"
DOMAIN_PATH="${BASE_PATH}domains/"
CONFIG_PATH="${BASE_PATH}config/"
AMAVIS_FILE="/etc/amavis/conf.d/90-schranz"

merge() {
	cat ${CONFIG_CACHE_PATH}*/$1 > ${CONFIG_PATH}$1
}

if [ ${DOMAIN_PATH} -nt ${AMAVIS_DOMAIN_FILE} ]; then
	cat ${DOMAIN_PATH}* | awk 'BEGIN{ ORS=" "; print "@local_domains_acl = ("; }{ print "\"" $0 "\""; }END{ print ");\n1;"; }' > ${AMAVIS_FILE}
	#service amavis restart
fi

if [ ${CONFIG_CACHE_PATH} -nt ${CONFIG_PATH} ]; then
	MAPS="account_maps alias_maps catchall_maps domain_maps"

	for f in ${MAPS}; do
		merge $f
		postmap "hash:${CONFIG_PATH}${f}"
	done

	merge passwd
	#service postfix reload
	#service dovecot reload
fi
