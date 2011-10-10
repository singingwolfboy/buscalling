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
