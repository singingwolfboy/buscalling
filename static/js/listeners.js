$().ready(function() {
    var model = window.app.model,
        option_template = '<option value="{0}">{1}</option>',
        option_blank = '<option value></option>',
        agency_elmt = $("form #agency"),
        route_elmt = $("form #route"),
        direction_elmt = $("form #direction"),
        stop_elmt = $("form #stop"),
        loader_icon = $('<img src="/img/ajax-loader.gif"/>'); // preload img

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
            dir_stop_list = model[agency].routes[route].directions[direction].stop_ids,
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
            $(".form_field.agency").append(loader_icon);
            $.getJSON('/{0}/routes.json'.format(agency), function(data) {
                $(".form_field.agency img").remove()
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
            $(".form_field.route").append(loader_icon);
            $.getJSON('/{0}/routes/{1}.json'.format(agency, route), function(data) {
                $(".form_field.route img").remove();
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

    $("input[type=time]").timePicker({
        defaultSelected: "07:00",
    });

    // Alerts
    window.app.alerts = [];
    window.app.alerts.addFromHTML = function (elmt) {
        window.app.alerts.push({
            "id": parseInt($(elmt).attr("id").match(/\d+/)[0], 10),
            "medium": $("input.alerts-medium", elmt).val(),
            "minutes": parseInt($("input.alerts-minutes", elmt).val())
        })
    }
    $("ul#alerts-list li").each(function () {
        window.app.alerts.addFromHTML(this);
    });

    $(".add-alert").live('click', function () {
        var li =  $(this).parentsUntil("ul#alerts-list").last(),
            opt = $("option:selected", li).val(),
            new_alert = li.clone(),
            elmts = new_alert.find("*").andSelf(),
            l = window.app.alerts.length;
        $.each(["id", "name", "for"], function(i, attrName) {
            elmts.attr(attrName, function (i, oldAttr) {
                if(oldAttr) {
                    return oldAttr.replace(/\d+/, l);
                }
            });
        })
        $("select.alerts-medium option[value="+opt+"]", new_alert).attr("selected", "selected");
        window.app.alerts.addFromHTML(new_alert);
        $("#alerts-list").append(new_alert);
        if (window.app.alerts.length > 1) {
            $("ul#alerts-list li input.delete-alert").each(function() {
                $(this).attr('disabled', false);
            })
        }
        return window.app.alerts.length;
    });
    $(".delete-alert").live('click', function () {
        var li = $(this).parentsUntil("ul#alerts-list").last(),
            id = parseInt(li.attr("id").match(/\d+/)[0], 10);
        delete window.app.alerts[id];
        li.remove();
        // if we have only one alert left, disable the delete button
        if (_.compact(window.app.alerts).length== 1) {
            $(".delete-alert").first().attr('disabled', true);
        }
    })
})