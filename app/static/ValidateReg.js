function ValidateReg() {
                     
                    var flag = 1;
                     
                    if(document.getElementsByName('firstname')[0].value.replace(/\s/g,"") == "")
                    {
                    alert('Please enter your first name!');
                    return false;
                    };
                     
                    if(document.getElementsByName('lastname')[0].value.replace(/\s/g,"") == "") {
                    alert('Please enter your last name!!');
                    return false;
                    };
                    if(document.getElementsByName('username')[0].value.replace(/\s/g,"") == "") {
                    alert('Please enter a User Name!');
                    return false;
                    };
                    if(document.getElementsByName('email')[0].value.replace(/\s/g,"") == "") {
                    alert('Please enter your email!');
                    return false;
                    };
                    if(document.getElementsByName('password')[0].value.replace(/\s/g,"") == "") {
                    alert('Please enter a password!');
                    return false;
                    };
                    if(document.getElementsByName('passwordconfirm')[0].value.replace(/\s/g,"") == "") {
                    alert('Please confirm your password!');
                    return false
                    };
                    

                    if(document.getElementsByName('password')[0].valuereplace(/\s/g,"") != document.getElementsByName('passwordconfirm')[0].valuereplace(/\s/g,"")) {
                    alert("Passwords don't match!");
                    return false;
                    };

                     
                    if(flag == 0) {
                    return false;
                    } else {
                    return true;
                    };
                     
                    };

                    