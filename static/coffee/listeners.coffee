window.App = window.App || {} # hold instances

$().ready ->
  $.ajaxSetup
    headers:
      "X-Limit": 0
  _.templateSettings = {
    interpolate : /\{\{(.+?)\}\}/g,
    evaluate : /\{\%(.+?)\%\}/g
  }

  class window.Listener         extends Backbone.RelationalModel
    defaults:
      agency: null
      route: null
      direction: null
      stop: null
    relations: [{
      type: Backbone.HasOne
      key: 'agency'
      relatedModel: 'Agency'
    }, {
      type: Backbone.HasOne
      key: 'route'
      relatedModel: 'Route'
    }, {
      type: Backbone.HasOne
      key: 'direction'
      relatedModel: 'Direction'
    }, {
      type: Backbone.HasOne
      key: 'stop'
      relatedModel: 'Stop'
    }, {
      type: Backbone.HasMany
      key: 'scheduled_notifications'
      relatedModel: 'ScheduledNotification'
      collectionType: 'ScheduledNotificationList'
      reverseRelation: {
        key: 'listener'
      }
    }]

    initialize: ->
      @bind('change:agency', @changeAgency, @)
      @bind('change:route', @changeRoute, @)
      @bind('change:direction', @changeDirection, @)
      @bind('change:stop', @changeStop, @)

    changeAgency: (listener, agency) ->
      prevAgency = listener.previous("agency")
      if prevAgency != agency
        prevAgency?.set("focused": false)
        agency?.set("focused": true)
        listener.set("route": null).set("direction": null).set("stop": null)

    changeRoute: (listener, route) ->
      prevRoute = listener.previous("route")
      if prevRoute != route
        if prevRoute
          prevRoute.set("focused": false)
          prevRoute.unbind("change", @triggerRouteChange)
        if route
          route.set("focused": true)
          route.bind("change", @triggerRouteChange, @)
        listener.set("direction": null).set("stop": null)

    triggerRouteChange: =>
      prevRoute = @previous("route")
      route = @get("route")
      if route
        prevDirections = prevRoute.get('directions')
        if prevDirections?.length
          route.set('directions', prevDirections)
        else
          route.get('directions').fetch()
        @trigger("change:route", @, route)

    changeDirection: (listener, direction) ->
      prevDirection = listener.previous("direction")
      if prevDirection != direction
        prevDirection?.set("focused": false)
        direction?.set("focused": true)
        listener.set("stop": null)

    changeStop: (listener, stop) ->
      prevStop = listener.previous("stop")
      if prevStop != stop
        prevStop?.set("focused": false)
        stop?.set("focused": true)

  class window.ScheduledNotification     extends Backbone.RelationalModel
    defaults:
      medium: "phone"
      minutes: 5

  class window.AbstractModel    extends Backbone.RelationalModel
    # name required
    defaults:
      id: ""
      title: ""
      focused: false
    url: -> @get('resource_uri')
    sync: Backbone.memoized_sync
    initialize: ->
      @bind('change:focused', @focusChange, @)
    focusChange: (model, focused) ->
      if focused
        o = {}
        o[@name.toLowerCase()] = model
        App.listener.set(o)
  
  class window.Agency           extends AbstractModel
    name: "Agency"
    relations: [{
      type: Backbone.HasMany
      key: 'routes'
      relatedModel: 'Route'
      collectionType: 'RouteList'
      reverseRelation: {
        key: 'agency'
      }
    }]

  class window.Route            extends AbstractModel
    name: "Route"
    relations: [{
      type: Backbone.HasMany
      key: 'directions'
      relatedModel: 'Direction'
      collectionType: 'DirectionList'
      reverseRelation: {
        key: 'route'
      }
    }]

  class window.Direction        extends AbstractModel
    name: "Direction"
    relations: [{
      type: Backbone.HasMany
      key: 'stops'
      relatedModel: 'Stop'
      collectionType: 'StopList'
      reverseRelation: {
        key: 'direction'
      }
    }]

  class window.Stop             extends AbstractModel
    name: "Stop"

  class window.ScheduledNotificationList     extends Backbone.Collection
    model: ScheduledNotification

  class window.AbstractCollection   extends Backbone.Collection
    sync: Backbone.memoized_sync
    order: []
    comparator: (model) =>
      id = model.get("id")
      return unless id
      index = @order.indexOf(id)
      if index < 0
        index = @order.length
        @order.push(id)
      return index

    initialize: ->
      @bind('reset', @onReset, @)

    onReset: (models) ->
      @order = models.pluck("id")
      if @xhr and @xhr.state() == "pending"
        @xhr.abort()
      o = {}
      o[@model.name.toLowerCase()] = null
      App.listener.set(o)

  class window.AgencyList           extends AbstractCollection
    model: Agency
    url: "/agencies"

  class window.RouteList            extends AbstractCollection
    model: Route
    url: ->
      @agency.url() + "/routes"

  class window.DirectionList        extends AbstractCollection
    model: Direction
    url: ->
      @route.url() + "/directions"

  class window.StopList             extends AbstractCollection
    model: Stop
    url: ->
      @direction.url() + "/stops"

  ### Templates and Views ###
  class MapView                 extends Backbone.View
    el: "#map_canvas"
    initialize: ->
      @m = google.maps
      @model.bind('change:agency', @onAgencyChange, @)
      @model.bind('change:route', @onRouteChange, @)
      @model.bind('change:stop', @onStopChange, @)
      @render()
    render: ->
      @map = new @m.Map(@el,
        zoom: 3
        center: new @m.LatLng(37.0625, -95.677068) # USA
        mapTypeId: @m.MapTypeId.ROADMAP
        disableDefaultUI: true
      )
      @onAgencyChange(App.listener, App.listener.get('agency'))
      @onRouteChange(App.listener, App.listener.get('route'))
      @onStopChange(App.listener, App.listener.get('stop'))

    onAgencyChange: (listener, agency) ->
      if agency
        minPt = agency.get("min_pt")
        maxPt = agency.get("max_pt")
        if minPt?.length and maxPt?.length
          bounds = new @m.LatLngBounds(
            new @m.LatLng(minPt[0], minPt[1]),
            new @m.LatLng(maxPt[0], maxPt[1]),
          )
          @map.fitBounds(bounds)
      @map

    onRouteChange: (listener, route) ->
      if @map.route
        for polyline in @map.route
          polyline.setMap(null)
      if route
        minPt = route.get("min_pt")
        maxPt = route.get("max_pt")
        if minPt?.length and maxPt?.length
          bounds = new @m.LatLngBounds(
            new @m.LatLng(minPt[0], minPt[1]),
            new @m.LatLng(maxPt[0], maxPt[1]),
          )
          @map.fitBounds(bounds)
        paths = route.get("paths")
        if paths
          route = []
          for subpath in paths
            latlngs = [new @m.LatLng(point[0], point[1]) for point in subpath]
            route.push(new @m.Polyline(
              path: latlngs
              map: @map
            ))
          @map.route = route
      else
        @map.route = []
      @map

    onStopChange: (listener, stop) ->
      if @map.stop
        @map.stop.setMap(null)
      if stop
        point = stop.get("point")
        @map.stop = new @m.Marker
          position: new @m.LatLng point[0], point[1]
          title: stop.get("name")
          map: @map
      else
        @map.stop = null
      if @map.stop
        @map.panTo(@map.stop.getPosition())
        @map.setZoom(16)
      @map

  class TimeView                extends Backbone.View
    el: ".form_field.start input"
    initialize: ->
      @render()
    render: ->
      this.$(@el).timePicker
        defaultSelected: "7:00 AM"
        show24Hours: false

    events:
      "change": "updateTime"
    updateTime: ->
      time = this.$(@el).val()
      @model.set("start": time)

  fieldTemplate = _.template("""
    <label for="{{id}}">{{name}}</label>
    <select id="{{id}}" name="{{id}}_id" required>
      <option value=""></option> 
      {{options}}
    </select>
  """)
  optionTemplate = _.template("""
    <option value="{{id}}"{% if(focused) { %} selected="selected"{% } %}>{{name}}</option>
  """)
  class SelectorView            extends Backbone.View
    className: "form_field"
    id: -> @collection.model.name.toLowerCase() + "_id"
    render: ->
      if @collection
        options = @collection.map (model) ->
          optionTemplate(model.toJSON())
      else
        options = []
      $(this.el).html(fieldTemplate(
        id: @collection.model.name.toLowerCase()
        name: @collection.model.name
        options: options.join("")
      ))
      return this

    initialize: ->
      if @collection
        @collection.bind('reset', @render, @)
        @collection.bind('change:focused', @onFocus, @)
      @render()

    setCollection: (collection) ->
      return if @collection == collection
      if @collection
        @collection.unbind('reset', @render)
        @collection.unbind('change:focused', @onFocus)
      @collection = collection
      if @collection
        @collection.bind('reset', @render, @)
        @collection.bind('change:focused', @onFocus, @)
      @render()

    events:
      "change select": "changeSelect"
    
    changeSelect: ->
      id = this.$("select").val()
      o = {}
      o[@collection.model.name.toLowerCase()] = @collection.get(id)
      App.listener.set(o)
  
  class AgencySelectorView      extends SelectorView
    el: "#bus-info .form_field.agency"
    collection: App.agencies

    onFocus: (agency, focused) ->
      if focused
        routes = agency.get('routes')
        App.routesView.setCollection(routes)
        if routes
          # Don't fetch paths for the collection: it's too much information.
          # We'll fetch the "paths" attribute when a route is selected.
          routes.xhr = routes.fetch(
            headers:
              "X-Limit": 0
              "X-Exclude": "paths"
          )
      else
        App.routesView.collection.reset()
      App.directionsView.collection.reset()
      App.stopsView.collection.reset()
      @render()

  class RouteSelectorView       extends SelectorView
    el: "#bus-info .form_field.route"

    onFocus: (route, focused) ->
      if focused
        collection = route.collection
        route.xhr = route.fetch( # get "paths" attribute
          success: ->
            collection.add(route)
        )
        directions = route.get('directions')
        App.directionsView.setCollection(directions)
        directions.xhr = directions.fetch() if directions
      else
        App.directionsView.collection.reset()
      App.stopsView.collection.reset()
      @render()

  class DirectionSelectorView   extends SelectorView
    el: "#bus-info .form_field.direction"

    onFocus: (direction, focused) ->
      if focused
        stops = direction.get('stops')
        App.stopsView.setCollection(stops)
        stops.xhr = stops.fetch() if stops
      else
        App.stopsView.collection.reset()
      @render()

  class StopSelectorView        extends SelectorView
    el: "#bus-info .form_field.stop"

    onFocus: ->
      @render()
  
  ### Router ###
  class window.Router           extends Backbone.Router
    routes:
      ":agency_id" :                                "setAgency"
      ":agency_id/:route_id" :                      "setRoute"
      ":agency_id/:route_id/:direction_id" :        "setDirection"
      ":agency_id/:route_id/:direction_id/:stop_id":"setStop"
    
    setAgency: (agency_id) ->
      App.listener.set("agency": App.agencies.get(agency_id))
    setRoute: (agency_id, route_id) ->
      @setAgency(agency_id)
      App.listener.set("route": App.routes.get(route_id))
    setDirection: (agency_id, route_id, direction_id) ->
      @setRoute(agency_id, route_id)
      App.listener.set("direction": App.directions.get(direction_id))
    setStop: (agency_id, route_id, direction_id, stop_id) ->
      @setDirection(agency_id, route_id, direction_id)
      App.listener.set("stop", App.stops.get(stop_id))

    initialize: ->
      App.mapView = new MapView(model: App.listener)
      App.timeView = new TimeView(model: App.listener)
      App.agenciesView = new AgencySelectorView(collection: App.agencies)
      App.routesView = new RouteSelectorView(collection: App.routes)
      App.directionsView = new DirectionSelectorView(collection: App.directions)
      App.stopsView = new StopSelectorView(collection: App.stops)

  # Create these outside of the Router initialize function, so that 
  # they are created *first*
  App.listener = new Listener
  App.agencies = new AgencyList
  App.routes = new RouteList
  App.directions = new DirectionList
  App.stops = new StopList
  
  ###
  # kick off the app
  App.router = new Router
  Backbone.history.start()
  ###

  
###

  
  model = window.app.model
  option_fill = (title, value) ->
    "<option value=\"#{value}\">#{title}</option>"
  option_blank = "<option value></option>"
  agency_elmt = $("form #agency")
  route_elmt = $("form #route")
  direction_elmt = $("form #direction")
  stop_elmt = $("form #stop")
  loader_icon = $("<img src=\"/static/ajax-loader.gif\"/>")

  # Google Map
  window.app.map = new google.maps.Map $("#map_canvas").get(0), 
    zoom: 10,
    center: new google.maps.LatLng(42.373, -71.111), # cambridge
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    disableDefaultUI: true
  map = window.app.map
  map.active = {} # hold state

  update_routes = (agency) ->
    routes = [ option_blank ]
    # JS objects don't have a defined ordering, so we've defined that ordering as
    # a ._order array, which contains the route IDs in the order we want. Loop
    # through the array, and for each ID, pull the appropriate route from the JS
    # object.
    for id in model[agency].routes._order
      route = model[agency].routes[id]
      routes.push option_fill(route.title, id)
    route_elmt.children().replaceWith $(routes.join(""))
  
  update_directions = (agency, route) ->
    directions = [ option_blank ]
    dir_info = model[agency].routes[route].directions
    for dir_id of dir_info
      directions.push option_fill(dir_info[dir_id].title, dir_id)
    direction_elmt.children().replaceWith $(directions.join(""))
  
  update_stops = (agency, route, direction) ->
    stops = [ option_blank ]
    stop_info = model[agency].routes[route].stops
    for id in model[agency].routes[route].directions[direction].stop_ids
      stops.push option_fill(stop_info[id].title, id)
    
    stop_elmt.children().replaceWith $(stops.join(""))
  
  clear_select = (elmt) ->
    elmt.children().replaceWith $(option_blank)

  update_map = (options) ->
    m = google.maps
    if options.stop
      stop = model[options.agency].routes[options.route].stops[options.stop] 
      if not stop.marker
        stop.marker = new m.Marker
          position: new m.LatLng stop.lat, stop.lng
          title: stop.title
          map: map
      if map.active.stop
        map.active.stop.setVisible(false)
      stop.marker.setVisible(true)
      map.active.stop = stop.marker
      map.panTo(map.active.stop.getPosition())
      map.setZoom(16)
      return map

    if options.route
      route = model[options.agency].routes[options.route]
      if not route.bounds
        route.bounds = new m.LatLngBounds(
          new m.LatLng(route.latMin, route.lngMin),
          new m.LatLng(route.latMax, route.lngMax)
        )
      map.fitBounds(route.bounds)
      if not route.polylines
        polylines = []
        for subpath in route.path
          if not subpath.polyline
            latlngs = []
            for point in subpath
              if not point.latlng
                point.latlng = new m.LatLng(point.lat, point.lng)
              latlngs.push(point.latlng)
            subpath.polyline = new m.Polyline
              path: latlngs
              map: map
          polylines.push(subpath.polyline)
        route.polylines = polylines
      if map.active.route
        for polyline in map.active.route
          polyline.setMap(null)
      map.active.route = route.polylines
      for polyline in map.active.route
        polyline.setMap(map)
      if map.active.stop
        map.active.stop.setVisible(false)
      return map
  
  agency_elmt.change ->
    clear_select(elmt) for elmt in [ route_elmt, direction_elmt, stop_elmt ]
    agency = agency_elmt.val()
    if model[agency].routes
      update_routes(agency)
    else
      $(".form_field.agency").append loader_icon
      $.getJSON "/#{agency}/routes.json", (data) ->
        $(".form_field.agency img").remove()
        model[agency].routes = data
        update_routes(agency)
  
  route_elmt.change ->
    clear_select(elmt) for elmt in [ direction_elmt, stop_elmt ]
    agency = agency_elmt.val()
    route = route_elmt.val()
    if model[agency].routes[route].directions
      update_directions agency, route
      update_map
       agency: agency
       route: route
    else
      $(".form_field.route").append loader_icon
      $.getJSON "/#{agency}/routes/#{route}.json", (data) ->
        $(".form_field.route img").remove()
        model[agency].routes[route] = data
        update_directions agency, route
        update_map
          agency: agency
          route: route
  
  direction_elmt.change ->
    _.each [ stop_elmt ], clear_select
    agency = agency_elmt.val()
    route = route_elmt.val()
    direction = direction_elmt.val()
    update_stops agency, route, direction

  stop_elmt.change ->
    update_map
      agency: agency_elmt.val()
      route: route_elmt.val()
      direction: direction_elmt.val()
      stop: stop_elmt.val()
  
  $(".form_field.start input").timePicker(
    defaultSelected: "7:00 AM"
    show24Hours: false
  )
  window.app.notifications = []
  window.app.notifications.addFromHTML = (elmt) ->
    window.app.notifications.push 
      id: parseInt($(elmt).attr("id").match(/\d+/)[0], 10)
      medium: $("input.notifications-medium", elmt).val()
      minutes: parseInt($("input.notifications-minutes", elmt).val(), 10)
  
  $("ul#notifications-list li").each ->
    window.app.notifications.addFromHTML this
  
  $(".add-notification").live "click", ->
    li = $(this).parentsUntil("ul#notifications-list").last()
    opt = $("option:selected", li).val()
    new_notification = li.clone()
    elmts = new_notification.find("*").andSelf()
    l = window.app.notifications.length
    for attrName in [ "id", "name", "for" ]
      elmts.attr(attrName, (i, oldAttr) ->
        oldAttr.replace /\d+/, l  if oldAttr
      )
    
    $("select.notifications-medium option[value=#{opt}]", new_notification).attr("selected", "selected")
    window.app.notifications.addFromHTML new_notification
    $("#notifications-list").append new_notification
    if window.app.notifications.length > 1
      $("ul#notifications-list li input.delete-notification").each ->
        $(this).attr "disabled", false
    window.app.notifications.length
  
  $(".delete-notification").live "click", ->
    li = $(this).parentsUntil("ul#notifications-list").last()
    id = parseInt(li.attr("id").match(/\d+/)[0], 10)
    delete window.app.notifications[id]
    
    li.remove()
    if _.compact(window.app.notifications).length == 1
      $(".delete-notification").first().attr("disabled", true)

  $("#recur input[type=radio]").change ->
    if this.value == "y"
      $("#dates-label-plural").show()
      $("#dates-label-singular").hide()
      $("#week_checkboxes").show()
      $("#dow").hide()
    else
      $("#dates-label-singular").show()
      $("#dates-label-plural").hide()
      $("#dow").show()
      $("#week_checkboxes").hide()
  
  $(".form_field img.help_icon").each ->
    help_text = $(this).siblings(".help_text")
    $(this).toggle (->
      help_text.show "fast"
    ), (->
      help_text.hide "fast"
    )
  
  $(".notifications-medium").live "change", ->
    if this.value == "txt"
      $("#sms-warning").show "fast"
      return
    if _.all( $(".notifications-medium"), (select) -> select.value != "txt" )
      $("#sms-warning").hide "fast"

###
