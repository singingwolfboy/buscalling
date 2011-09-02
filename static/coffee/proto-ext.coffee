"use strict" # Strict mode, see http://ejohn.org/blog/ecmascript-5-strict-mode-json-and-more/

###
  orderedLoop()
Iterate through an object's properties, similar to a "for in" loop.
However, automatically checks hasOwnProperty, and you can specify
an ordering by setting an "_order" property that contains an array
of property names.
###
window.orderedLoop = (obj, fun) ->
  throw new TypeError("first arg cannot be null")  if obj == undefined or obj == null
  throw new TypeError("second argument must be a function")  unless _.isFunction(fun)
  throw new TypeError("missing _order attribute")  unless _.isArray(obj._order)
  thisp = arguments[1]
  _.each obj._order, (key, i) ->
    fun.call thisp, key, obj[key], i, obj  if obj.hasOwnProperty(key)