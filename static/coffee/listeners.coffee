$().ready ->
  $.ajaxSetup
    headers:
      "X-Limit": 0

  window.App = {} # instances
  
  ### Models  ###
  class window.Stop             extends Backbone.RelationalModel
    url: -> @get('url')

  class window.Direction        extends Backbone.RelationalModel
    url: -> @get('url')
    relations: [{
      type: Backbone.HasMany
      key: 'stops'
      relatedModel: 'Stop'
      collectionType: 'StopList'
      reverseRelation: {
        key: 'direction'
      }
    }]

  class window.Route            extends Backbone.RelationalModel
    url: -> @get('url')
    relations: [{
      type: Backbone.HasMany
      key: 'directions'
      relatedModel: Direction
      collectionType: 'DirectionList'
      reverseRelation: {
        key: 'route'
      }
    }]

  class window.Agency           extends Backbone.RelationalModel
    url: -> @get('url')
    relations: [{
      type: Backbone.HasMany
      key: 'routes'
      relatedModel: Route
      collectionType: 'RouteList'
      reverseRelation: {
        key: 'agency'
      }
    }]

  ### Collections ###
  class window.StopList         extends Backbone.Collection
    model: Stop
    url: -> "#{@direction.url()}/stops"
  
  class window.DirectionList    extends Backbone.Collection
    model: Direction
    url: -> "#{@route.url()}/directions"

  class window.RouteList        extends Backbone.Collection
    model: Route
    url: -> "#{@agency.url()}/routes"

  class window.AgencyList       extends Backbone.Collection
    model: Agency
    url: "/agencies"

  App.agencies = new AgencyList

  ### Templates and Views ###
  fieldTemplate = _.template("""
    <label for="{{id}}">{{name}}</label>
    <select id="{{id}}" name="{{id}}_id" required>{{options}}</select>
  """)
  optionTemplate = _.template("""
    <option value="{{value}}">{{title}}</option>
  """)
  class SelectorView            extends Backbone.View
    # type is required: agency, route, direction, or stop
    name: -> @type.capitalize()
    className: "form_field"
    id: -> "#{@type}_id"
    render: ->
      options = this.models.map (model) ->
        optionTemplate(model.toJSON())
      $(this.el).html(fieldTemplate(
        id: @type
        name: @name
        options: options.join("")
      ))
      return this
    
    events:
      "change select": "changeSelect"
    
    changeSelect: ->
      id = this.$("select").val()
      this.models.get(id).trigger("activate")
  
  class StopSelectorView        extends SelectorView
    type: "stop"
    models: App.stops
  class DirectionSelectorView   extends SelectorView
    type: "direction"
    models: App.directions
  class RouteSelectorView       extends SelectorView
    type: "route"
    models: App.routes
  class AgencySelectorView      extends SelectorView
    type: "agency"
    models: App.agencies
  
  ### Router ###
  class Router                  extends Backbone.Router
    routes:
      ":agency" :                       "setAgency"
      ":agency/:route" :                "setRoute"
      ":agency/:route/:direction":      "setDirection"
      ":agency/:route/:direction/:stop":"setStop"
    
    # stubs
    setAgency: -> @
    setRoute: -> @
    setDirection: -> @
    setStop: -> @
  
  # kick off the app
  App.router = new Router

  
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
