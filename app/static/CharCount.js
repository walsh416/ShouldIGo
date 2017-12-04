//script to max out charachter limit
    function CharLimit(input, maxChar) {
        var len = $(input).val().length;
        $('#textCounter').text(maxChar - len + ' characters remaining');
        
        if (len > maxChar) {
            $(input).val($(input).val().substring(0, maxChar));
            $('#textCounter').text(0 + ' characters remaining');
        }
    }
