#!/bin/bash
if [ -z $1 ] ; then
    ROOT=`pwd`
else
    ROOT=$1
fi
COMPASS="/Users/singingwolfboy/clones/compass/frameworks/compass/stylesheets"

# http://reinout.vanrees.org/weblog/2009/08/14/readline-invisible-character-hack.html
export TERM="linux"

trap "kill 0" EXIT
coffee -o $ROOT/static/js -w $ROOT/static/coffee &
watchmedo-2.7 shell-command --patterns="*.scss" \
    --command=$ROOT/compile-assets.sh \
    $ROOT/static/scss &
wait

