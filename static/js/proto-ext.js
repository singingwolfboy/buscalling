"use strict"; // Strict mode, see http://ejohn.org/blog/ecmascript-5-strict-mode-json-and-more/

//
// Standard extensions
//
if (!Array.prototype.forEach) {
  Array.prototype.forEach = function(fun /*, thisp */) {
    if (this === void 0 || this === null)
      throw new TypeError();

    var t = Object(this);
    var len = t.length >>> 0;
    if (typeof fun !== "function")
      throw new TypeError();

    var thisp = arguments[1];
    for (var i = 0; i < len; i++) {
      if (i in t) {
        fun.call(thisp, t[i], i, t);
      }
    }
  };
}

////////////////////////////
// Nonstandard extensions //
////////////////////////////

/**  orderedLoop()
 * Iterate through an object's properties, similar to a "for in" loop.
 * However, automatically checks hasOwnProperty, and you can specify
 * an ordering by setting an "_order" property that contains an array
 * of property names.
 */
window.orderedLoop = function(obj, fun /*, thisp */) {
  if (obj === void 0 || obj === null)
    throw new TypeError();
  if (typeof fun !== "function")
    throw new TypeError();
  if (!(typeof obj._order == "object" && obj._order instanceof Array)) 
    throw new TypeError("missing _order attribute")
  
  var thisp = arguments[1];
  obj._order.forEach(function(key, i) {
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
        context.forEach(function (val, i) {
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
      var i=0, l=arguments.length;
      for(;i<l;i++) {
        ret = ret.split("{"+i+"}").join(arguments[i])
      }
    }
    return ret
  };
}