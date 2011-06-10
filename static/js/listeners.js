$().ready(function() {
    var option_template = '<option value="{0}">{1}</option>',
        option_blank = '<option value></option>';
    var update_routes = function(agency) {
        var routes = [option_blank]
        orderedLoop(model[agency].routes, function (id, route) {
            routes.push(option_template.format(id, route["title"]))
        })
        $("form #route option").replaceWith($(routes.join("")));
    };
    var update_directions = function(agency, route) {
        var directions = [option_blank],
            dir_info = model[agency].routes[route].directions,
            dir_id;
        for(dir_id in dir_info) {
            directions.push(option_template.format(dir_id, dir_info[dir_id]["title"]));
        }
        $("form #direction option").replaceWith($(directions.join("")));
    }
    var update_stops = function(agency, route, direction) {
        var stops = [option_blank],
            dir_stop_list = model[agency].routes[route].directions[direction].stops,
            stop_info = model[agency].routes[route].stops;
        dir_stop_list.forEach(function(id) {
            stops.push(option_template.format(id, stop_info[id]["title"]));
        })
        $("form #stop option").replaceWith($(stops.join("")));
    }

    $('form #agency').live('change', function () {
        $('form #stop option').replaceWith($(option_blank));
        $('form #direction option').replaceWith($(option_blank));

        var agency = this.value
        if(model[agency].routes) {
            update_routes(agency)
        } else {
            $.getJSON('/{0}/routes.json'.format(agency), function(data) {
                model[agency].routes = data
                update_routes(agency)
            })
        }
    })
    $('form #route').live('change', function () {
        $('form #stop option').replaceWith($(option_blank));

        var agency = $('form #agency').val(),
            route  = this.value
        if(model[agency].routes[route].directions) {
            update_directions(agency, route)
        } else {
            $.getJSON('/{0}/routes/{1}.json'.format(agency, route), function(data) {
                model[agency].routes[route] = data
                update_directions(agency, route)
            })
        } 
    })
    $('form #direction').live('change', function () {
        var agency = $('form #agency').val(),
            route  = $('form #route').val(),
            direction = this.value;
        update_stops(agency, route, direction);
    })
})