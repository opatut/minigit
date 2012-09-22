$(document).ready(function() {
    $("#branch-select").change(function() {
        window.location = $(this).val();
    });
});

