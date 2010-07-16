#!/bin/sh

BASE_PATH="/var/lib/schranz/mail/"
CONFIG_CACHE_PATH="${BASE_PATH}cache/"
DOMAIN_PATH="${BASE_PATH}domains/"
CONFIG_PATH="${BASE_PATH}config/"
AMAVIS_FILE="/etc/amavis/conf.d/90-schranz"

POSTMAP="/usr/sbin/postmap"

AWK_SCRIPT='
BEGIN {
	ORS="";
	print "@local_domains_acl = ( ";
}
{
	sub(/^[[:space:]]+|[[:space:]]+$/, "");
	if ($0 !~ /^[[:space:]]*$|^[#;]/) {
		if (notfirst) {
			print ", ";
		}
		print "\"" $0 "\"";
		notfirst = 1;
	}
}
END {
	print " );\n1;\n";
}'

merge() {
	cat ${CONFIG_CACHE_PATH}*/$1 > ${CONFIG_PATH}$1
}

if [ ${DOMAIN_PATH} -nt ${AMAVIS_FILE} ]; then
	echo "Reloading amavis config"
	cat ${DOMAIN_PATH}* | awk "$AWK_SCRIPT" > ${AMAVIS_FILE}
	service amavis restart 2>&1 > /dev/null
	touch  ${AMAVIS_FILE}
fi

if [ ${CONFIG_CACHE_PATH} -nt ${CONFIG_PATH} ]; then
	echo "Reloading postfix and dovecot config"
	MAPS="account_maps alias_maps catchall_maps domain_maps"

	for f in ${MAPS}; do
		merge $f
		${POSTMAP} "hash:${CONFIG_PATH}${f}"
	done

	merge passwd
	service postfix reload 2>&1 > /dev/null
	service dovecot reload 2>&1 > /dev/null
	touch ${CONFIG_PATH}
fi
