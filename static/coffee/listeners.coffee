$().ready ->
  model = window.app.model
  option_fill = (title, value) ->
    "<option value=\"#{value}\">#{title}</option>"
  option_blank = "<option value></option>"
  agency_elmt = $("form #agency")
  route_elmt = $("form #route")
  direction_elmt = $("form #direction")
  stop_elmt = $("form #stop")
  loader_icon = $("<img src=\"/static/ajax-loader.gif\"/>")

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
    else
      $(".form_field.route").append loader_icon
      $.getJSON "/#{agency}/routes/#{route}.json", (data) ->
        $(".form_field.route img").remove()
        model[agency].routes[route] = data
        update_directions agency, route
  
  direction_elmt.change ->
    _.each [ stop_elmt ], clear_select
    agency = agency_elmt.val()
    route = route_elmt.val()
    direction = direction_elmt.val()
    update_stops agency, route, direction
  
  $("input[type=time]").timePicker(defaultSelected: "07:00")
  window.app.alerts = []
  window.app.alerts.addFromHTML = (elmt) ->
    window.app.alerts.push 
      id: parseInt($(elmt).attr("id").match(/\d+/)[0], 10)
      medium: $("input.alerts-medium", elmt).val()
      minutes: parseInt($("input.alerts-minutes", elmt).val(), 10)
  
  $("ul#alerts-list li").each ->
    window.app.alerts.addFromHTML this
  
  $(".add-alert").live "click", ->
    li = $(this).parentsUntil("ul#alerts-list").last()
    opt = $("option:selected", li).val()
    new_alert = li.clone()
    elmts = new_alert.find("*").andSelf()
    l = window.app.alerts.length
    for attrName in [ "id", "name", "for" ]
      elmts.attr(attrName, (i, oldAttr) ->
        oldAttr.replace /\d+/, l  if oldAttr
      )
    
    $("select.alerts-medium option[value=#{opt}]", new_alert).attr("selected", "selected")
    window.app.alerts.addFromHTML new_alert
    $("#alerts-list").append new_alert
    if window.app.alerts.length > 1
      $("ul#alerts-list li input.delete-alert").each ->
        $(this).attr "disabled", false
    window.app.alerts.length
  
  $(".delete-alert").live "click", ->
    li = $(this).parentsUntil("ul#alerts-list").last()
    id = parseInt(li.attr("id").match(/\d+/)[0], 10)
    delete window.app.alerts[id]
    
    li.remove()
    if _.compact(window.app.alerts).length == 1
      $(".delete-alert").first().attr("disabled", true)

  $("#recur input[type=radio]").change ->
    if this.value == "y"
      $("#week_checkboxes").show()
      $("#week_radio").hide()
    else
      $("#week_radio").show()
      $("#week_checkboxes").hide()
