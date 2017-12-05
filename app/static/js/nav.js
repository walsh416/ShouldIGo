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
