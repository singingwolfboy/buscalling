//
// Backbone.memoized_sync 0.1.0
// ==========================
//
// Made by Pablo Villalba for the Teambox project
// May be freely distributed under the MIT license
//
//
// What does Backbone.memoized_sync solve
// --------------------------------------
//
// The default Backbone.sync sends an AJAX request every time. When an app needs to
// request too much data to start up, the UX can suffer.
//
// This modified version changes the behavior for 'read' requests to the following:
//
// 1. Check if we have it in localStorage.
// 2. If we have it, then...
//   - We call the success function with the cached data
//   - We request new data with an AJAX request, which calls the success function again
// 3. If we don't have it, we do a classic AJAX request and save its results to localStorage
//
//
// How to enabled memoized sync for your models and collections
// ------------------------------------------------------------
//
// You must define your model's or collection's sync to be Backbone.memoized_sync:
//
//     this.sync = Backbone.memoized_sync;
//
// That's it! Now every GET request will be written to localStorage and retrieved
// from there the next time you request it.
//
//
// Handling multiple sessions or users
// -----------------------------------
//
// In order to use this with per-session caches, you will need to define the
// *cache_namespace* attribute in your models and collections. The sync method will
// store the results of successful calls in "#{cache_namespace}/#{requested_url}"
//
// If you are caching sensitive data, remember to clear localStorage when logging out
// or when loggin in with a different user.
//
//
// Targeted Backbone versions
// --------------------------
// This modified Backbone.sync targets Backbone 0.5.3.
//

(function () {

  // Map from CRUD to HTTP for our default `Backbone.sync` implementation.
  var methodMap = {
    'create': 'POST',
    'update': 'PUT',
    'delete': 'DELETE',
    'read'  : 'GET'
  };

  // Helper function to get a URL from a Model or Collection as a property
  // or as a function.
  var getUrl = function(object) {
    if (!(object && object.url)) return null;
    return _.isFunction(object.url) ? object.url() : object.url;
  };

  // Ported from Modernizr
  function supports_local_storage() {
    try {
      return 'localStorage' in window && window.localStorage !== null;
    } catch (e) {
      return false;
    }
  }

  Backbone.memoized_sync = function (method, model, options) {
    var type = methodMap[method];

    // Default JSON-request options.
    var params = _.extend({
      type:         type,
      dataType:     'json'
    }, options);

    // Ensure that we have a URL.
    if (!params.url) {
      params.url = getUrl(model) || urlError();
    }

    // Ensure that we have the appropriate request data.
    if (!params.data && model && (method == 'create' || method == 'update')) {
      params.contentType = 'application/json';
      params.data = JSON.stringify(model.toJSON());
    }

    // For older servers, emulate JSON by encoding the request into an HTML-form.
    if (Backbone.emulateJSON) {
      params.contentType = 'application/x-www-form-urlencoded';
      params.data        = params.data ? {model : params.data} : {};
    }

    // For older servers, emulate HTTP by mimicking the HTTP method with `_method`
    // And an `X-HTTP-Method-Override` header.
    if (Backbone.emulateHTTP) {
      if (type === 'PUT' || type === 'DELETE') {
        if (Backbone.emulateJSON) params.data._method = type;
        params.type = 'POST';
        params.beforeSend = function(xhr) {
          xhr.setRequestHeader('X-HTTP-Method-Override', type);
        };
      }
    }

    // Don't process data on a non-GET request.
    if (params.type !== 'GET' && !Backbone.emulateJSON) {
      params.processData = false;
    }

    // This is the modified part:
    // - Look for the cached version and trigger success if it's present.
    // - Modify the AJAX request so it'll save the data on success.
    if (method === 'read' && supports_local_storage()) {
      // Look for the cached version
      var namespace = model.cache_namespace || "_",
          key = "backbone-cache/" + namespace + "/" + params.url,
          val = localStorage.getItem(key),
          successFn = params.success;

      // If we have the last response cached, use it with the success callback
      if (val) {
        _.defer(function () {
          successFn(JSON.parse(val), "success");
        });
      }

      // Overwrite the success callback to save data to localStorage
      params.success = function (resp, status, xhr) {
        successFn(resp, status, xhr);
        try {
          localStorage.setItem(key, xhr.responseText);
        } catch (e) {
          console.error(e)
        }
      };

    }

    // Make the request.
    return $.ajax(params);
  };

}).call(this);
