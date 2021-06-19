$(function(){
    //set status to true on load
    {% if active == "show_liked" %}
        $('#check')[0].MaterialSwitch.on();
    {% endif %}

    //toggle label
    $('#check input').change(function(){
        if($(this).is(':checked'))
        {
            $(this).next().text("Скрыть сохраненные события");
            document.location.href = '/show_liked/';
        }
        else
        {
            $(this).next().text("Показать сохраненные события");
            document.location.href = '/';
        }
    });
    $('.button-like').on('click', function() {
        var like_id = $(this).attr("id");
        var data = {like_id};
        //console.log(JSON.stringify(data));
        $.ajax({
            type: "POST", 
            url: "/like", //localhost Flask
            data : JSON.stringify(data),
            contentType: "application/json",
            success: function (data) {
                console.log(data);
            },
            error: function (data) {
                console.log(data);
            }
        });
        $(this).removeClass('mdl-color--white');
        $(this).removeClass('mdl-color-text--accent');
        $(this).addClass('mdl-color--accent');
        $(this).addClass('mdl-color-text--white');
        /*
        $.post('/like', {
            data: JSON.stringify(data),
          }, function(data) {
          console.log(data);
        });
        */
    });
});

