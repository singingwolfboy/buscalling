$().ready ->
    $("#tabs li").each ->
        name = $(this).attr('id').match(/\w+/)[0]
        $(this).toggle (->
            $("##{name}-dropdown").show()
        ), (->
            $("##{name}-dropdown").hide()
        )