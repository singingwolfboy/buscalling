////////////////////////////
// Nonstandard extensions //
////////////////////////////
"use strict"; // Strict mode, see http://ejohn.org/blog/ecmascript-5-strict-mode-json-and-more/


/**  orderedLoop()
 * Iterate through an object's properties, similar to a "for in" loop.
 * However, automatically checks hasOwnProperty, and you can specify
 * an ordering by setting an "_order" property that contains an array
 * of property names.
 */
window.orderedLoop = function(obj, fun /*, thisp */) {
  if (obj === void 0 || obj === null)
    throw new TypeError("first arg cannot be null");
  if (!_.isFunction(fun))
    throw new TypeError("second argument must be a function");
  if (!_.isArray(obj._order))
    throw new TypeError("missing _order attribute")
  
  var thisp = arguments[1];
  _.each(obj._order, function(key, i) {
    if (obj.hasOwnProperty(key)) {
      fun.call(thisp, key, obj[key], i, obj);
    }
  });
}


/**  String.format
 * String formatting like Python. Use {0}, {1}, etc in the format string
 * to refer to arguments to the format function. Alternatively, pass in
 * an object and use {property} to refer to property values.
 *
 * Not yet safe against multiple replacement. For example:
 * "{0}".format("{1}", "wrong") => "wrong"
 * Bug, or feature?
 */
if (!String.prototype.format) {
  String.prototype.format = function(context) {
    var ret = this
    if (typeof(context)== "object") {
      if (context instanceof Array) {
        _.each(context, function (val, i) {
          ret = ret.split("{"+i+"}").join(val);
        })
      } else {
        var key, val;
        for (key in context) {
            if(context.hasOwnProperty(key)) {
            val = context[key]
            if (val instanceof Function) {
              val = val()
            }
            ret = ret.split("{"+key+"}").join(val)
          }
        }
      }
    } else {
      for (var i=0, l=arguments.length; i<l; i++) {
        ret = ret.split("{"+i+"}").join(arguments[i])
      }
    }
    return ret
  };
}