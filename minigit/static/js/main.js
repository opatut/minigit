var clip = null;

$(document).ready(function() {
    $("*[data-clipboard-text]").each(function() {
        clip = new ZeroClipboard($(this), {
            moviePath: "/static/swf/ZeroClipboard.swf"
        });
        clip.on("complete", function(client, args) {
            alert("The URL was copied to your clipboard.");
            document.body.focus();
            document.body.click();
        } );
    });
});
