#!/bin/bash
if [ -z $1 ] ; then
    echo "Please provide path to project root as first argument"
    exit 1
fi

coffee -o $1/static/js/ -c $1/static/coffee/
for f in $1/static/scss/*.scss
  do
    base=`basename $f .scss`
    if [ ${base:0:1} != "_" ] ; then
        pyscss -o $1/static/css/$base.css $f
    fi
done
