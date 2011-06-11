$().ready(function() {
    var model = window.app.model,
        option_template = '<option value="{0}">{1}</option>',
        option_blank = '<option value></option>',
        agency_elmt = $("form #agency"),
        route_elmt = $("form #route"),
        direction_elmt = $("form #direction"),
        stop_elmt = $("form #stop");

    var update_routes = function(agency) {
        var routes = [option_blank]
        orderedLoop(model[agency].routes, function (id, route) {
            routes.push(option_template.format(id, route["title"]))
        })
        route_elmt.children().replaceWith($(routes.join("")));
    }
    var update_directions = function(agency, route) {
        var directions = [option_blank],
            dir_info = model[agency].routes[route].directions,
            dir_id;
        for(dir_id in dir_info) {
            directions.push(option_template.format(dir_id, dir_info[dir_id]["title"]));
        }
        direction_elmt.children().replaceWith($(directions.join("")));
    }
    var update_stops = function(agency, route, direction) {
        var stops = [option_blank],
            dir_stop_list = model[agency].routes[route].directions[direction].stops,
            stop_info = model[agency].routes[route].stops;
        dir_stop_list.forEach(function(id) {
            stops.push(option_template.format(id, stop_info[id]["title"]));
        })
        stop_elmt.children().replaceWith($(stops.join("")));
    }

    var clear_select = function(elmt) {
        elmt.children().replaceWith($(option_blank));
    }

    agency_elmt.change(function () {
        _.each([route_elmt, direction_elmt, stop_elmt], clear_select)

        var agency = agency_elmt.val()
        if(model[agency].routes) {
            update_routes(agency)
        } else {
            $.getJSON('/{0}/routes.json'.format(agency), function(data) {
                model[agency].routes = data
                update_routes(agency)
            })
        }
    })
    route_elmt.change(function () {
        _.each([direction_elmt, stop_elmt], clear_select)

        var agency = agency_elmt.val(),
            route  = route_elmt.val()
        if(model[agency].routes[route].directions) {
            update_directions(agency, route)
        } else {
            $.getJSON('/{0}/routes/{1}.json'.format(agency, route), function(data) {
                model[agency].routes[route] = data
                update_directions(agency, route)
            })
        } 
    })
    direction_elmt.change(function () {
        _.each([stop_elmt], clear_select)

        var agency = agency_elmt.val(),
            route  = route_elmt.val(),
            direction = direction_elmt.val();
        update_stops(agency, route, direction);
    })
})