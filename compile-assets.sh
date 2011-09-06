#!/bin/bash
if [ -z $1 ] ; then
    ROOT=`pwd`
else
    ROOT=$1
fi
COMPASS="/Users/singingwolfboy/clones/compass/frameworks/compass/stylesheets"
BOURBON="/Users/singingwolfboy/clones/bourbon/app/assets/stylesheets"

# http://reinout.vanrees.org/weblog/2009/08/14/readline-invisible-character-hack.html
export TERM="linux"

coffee -o $ROOT/static/js/ -c $ROOT/static/coffee/
for f in $ROOT/static/scss/*.scss
  do
    base=`basename $f .scss`
    if [ ${base:0:1} != "_" ] ; then
        pyscss -o $ROOT/static/css/$base.css -I $COMPASS -I $BOURBON $f
    fi
done
