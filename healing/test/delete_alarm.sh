for x in `ceilometer alarm-list |cut -f2 -d '|'|grep '^ [0-9a-z]'`; do ceilometer alarm-delete -a $x; done

