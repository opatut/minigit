$(document).ready(function() {
    $(".image-preview .mode").click(function() {
        var pv = $(this).parent().parent();

        pv.find("a").removeClass("active");

        $(this).parent("a").addClass("active");

        pv.parent()
            .removeClass("transparent")
            .removeClass("black")
            .removeClass("white")
            .addClass($(this).attr("data-mode"));
    });
});
