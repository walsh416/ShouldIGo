function checkFields() {
                     
                    var flag = 1;
                     
                    if(document.getElementsByName('eventName')[0].value.replace(/\s/g,"") == "")
                    {
                    alert('Please fill out an Event Name!');
                    return false;
                    };
                     
                    if(document.getElementsByName('eventDesc')[0].value.replace(/\s/g,"") == "") {
                    alert('Please fill out an event description!');
                    return false;
                    };
                    
                     
                    if(document.getElementsByName('datefilter')[0].value.replace(/\s/g,"") == "") {
                    alert('Please fill out dates!');
                    return false;
                    };
                     
                    if(flag == 0) {
                    return false;
                    } else {
                    return true;
                    };
                     
                    };

