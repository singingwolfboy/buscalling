$().ready(function() {
    //$("input#email").data("defaultValue", $("input#email").val())
    emailField = $("input#email")
    emailField.data("defaultValue", "email@example.com")
    if (emailField.val() == emailField.data("defaultValue")) {
        $("input#email").addClass("defaultValue")
    }
})

$("input#email").focus(function() {
    if($(this).val() == $(this).data("defaultValue")) {
        $(this).removeClass("defaultValue");
        $(this).val("")
    }
}).blur(function() {
    if($(this).val() == "") {
        $(this).addClass("defaultValue");
        $(this).val($(this).data("defaultValue"))
    }
});

$("#use_location").change(function() {
    var label = $("#location_label")
    if(this.checked) {
        label.text("Requesting location...")
        navigator.geolocation.getCurrentPosition(function(pos) {
            label.text("Got location. Thanks!")
            $("#location_lat").val(pos.coords.latitude)
            $("#location_long").val(pos.coords.longitude)
        }, function(err) {
            $("#use_location").checked = false;
            label.text("Could not get location")
        })
    } else {
        label.text("Include location?")
        $("#location_lat").val("")
        $("#location_long").val("")
    }
})