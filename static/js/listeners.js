$().ready(function() {
    $('form #agency').live('change', function () {
        var agency = this.value
        $.getJSON('/'+agency+'/routes.json', function(data) {
            alert('pre-agency')
            model[agency].routes = data
            alert("agency changed")
        })
    })
    $('form #route').live('change', function () {
        var agency = $('form #agency').val(),
            route  = this.value
        $.getJSON('/'+agency+'/routes/'+route + '.json', function(data) {
            if(!model[agency].routes) {
                model[agency].routes = {route: data}
            } else {
                model[agency].routes[route] = data
            }

            directions = ["<option value></option>"]
            data.forEach(function (direction, i) {
                directions.push('<option value="'+direction.id+'">'+direction.title+'</option>')
            })
            $("form #direction option").replaceWith($(directions.join("")));
        })
    })
})