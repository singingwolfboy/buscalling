#!/bin/bash
if [ -z $1 ] ; then
    echo "Please provide path to project root as first argument"
    exit 1
fi

trap "kill 0" EXIT
coffee -o $1/static/js -w $1/static/coffee &
watchmedo-2.7 shell-command --patterns="*.scss" \
    --command='dname=`dirname ${watch_src_path}`/../css; fname=`basename ${watch_src_path} .scss`; pyscss ${watch_src_path} > ${dname}/${fname}.css; echo "compiled ${watch_src_path}"' \
    $1/static/scss &
wait
