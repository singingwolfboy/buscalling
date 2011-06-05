if (!Array.prototype.forEach) {
  Array.prototype.forEach = function(fun /*, thisp */) {
    "use strict";

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

if (!String.prototype.format) {
  String.prototype.format = function(context) {
    "use strict";
    var ret = this
    if (typeof context == "object") {
      var key, val;
      for (key in context) {
        val = context[key]
        if (val instanceof Function) {
          continue
        }
        ret = ret.replace(RegExp("\\{"+key+"\\}", "g"), val)
      }
    } else {
      var i=0, l=arguments.length;
      for(;i<l;i++) {
        ret = ret.replace(RegExp("\\{"+i+"\\}", "g"), arguments[i])
      }
    }
    return ret
  };
}