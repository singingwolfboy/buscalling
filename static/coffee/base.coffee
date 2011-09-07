$().ready ->
    $("#tabs li").each ->
        tab = $(this)
        name = $(this).attr('id').match(/\w+/)[0]
        dropdown = $("##{name}-dropdown")
        tab.toggle (->
            dropdown.animate({
                bottom: -dropdown.height()
            }, 'fast', 'swing', ->
                $(".arrow", tab).text("▲")
            )
        ), (->
            dropdown.animate({
                bottom: 0
            }, 'fast', 'swing', ->
                $(".arrow", tab).text("▼")
            ) 
        )
    
    $("#profile-dropdown-cancel").click ->
        $("#profile-tab").click()
    $("#payment-dropdown-cancel").click ->
        $("#payment-tab").click()
    $("#auth-info .email").click ->
        $("#profile-tab").click()