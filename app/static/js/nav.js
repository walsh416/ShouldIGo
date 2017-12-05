$(document).ready(function(){
    $(".nav-link").mouseenter(function(){
        $floor = $("#" + $(this).attr('data-btn-target'));
        $floor.removeClass("bg-dark");
        $floor.addClass("bg-light");
    }).mouseleave(function(){
        $floor = $("#" + $(this).attr('data-btn-target'));
        $floor.removeClass("bg-light");
        $floor.addClass("bg-dark");
    });
});


$(window).scroll(function(){
    // console.log($(window).scrollTop());
    var fixheight = $("#mainnav").height();
    if($(window).scrollTop()>=fixheight){
        $("#mainnav").addClass("fixed-top");
        $("body").css("padding-top", $("#mainnav").height());
    }
    else{
        $("#mainnav").removeClass("fixed-top");
        $("body").css("padding-top", 0);
    }
});
