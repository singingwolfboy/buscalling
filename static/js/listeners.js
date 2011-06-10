$().ready(function() {
    var option_template = '<option value="{id}">{title}</option>';
    var update_routes = function(agency) {
        routes = ["<option value></option>"]
        model[agency].routes.forEach(function (route) {
            routes.push(option_template.format(route))
        })
        $("form #route option").replaceWith($(routes.join("")));
    };
    var update_directions = function(agency, route) {
        var directions = ["<option value></option>"],
            dir_info = model[agency].routes[route].directions,
            dir_id;
        for(dir_id in dir_info) {
            directions.push(option_template.format({"id":dir_id, "title":dir_info[dir_id]["title"]}));
        }
        $("form #direction option").replaceWith($(directions.join("")));
    }

    $('form #agency').live('change', function () {
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
})