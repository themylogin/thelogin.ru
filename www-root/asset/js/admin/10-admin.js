$(function(){
    var admin = function(){
        // Drag&Drop тэгов
        /*
        var $postTags = $(".post .footer .tags");
        if ($postTags.length)
        {
            $postTags.addClass("admin");
            $postTags.contents().filter(function(){return this.nodeType == Node.TEXT_NODE;}).remove();
            $postTags.append("<div class='clear'></div>");
            $postTags.sortable();

            var $tagcloud = $(".right-col .tagcloud").parent();
            $tagcloud.css("width", $tagcloud.width());
            $tagcloud.css("position", "fixed");
            $tagcloud.css("bottom", "-20px");
            $tagcloud.css("opacity", "0.8");
            $tagcloud.css("background", "#80BA47");
            $tagcloud.find("a").addClass("tagcloud-tag").draggable({ revert: "invalid", helper: "clone" });

            $postTags.droppable({
                accept  : ".tagcloud-tag",
                drop    : function(event, ui){
                    $(this).find("div.clear").remove();
                    $(this).append(ui.helper.clone().attr("style", "").attr("class", ""));
                    $(this).append("<div class='clear'></div>");
                }
            });
        }
        */

        // Создание нового поста
        if (["", "blog"].indexOf(document.location.toString().split("/").slice(3).join("")) != -1)
        {
            $(".feed-item:first").before(
                $("<div/>").css("marginBottom", "10px").append($("<a/>").attr("href", "#").css("color", "#80BA47").css("fontSize", "13px").css("fontWeight", "800").text("Создать новую запись").click(function(){
                    window.open("/admin/new/blog/", "", "toolbar=no,width=1024,height=768");
                    return false;
                }))
            );
        }
        
        // Редактирование поста
        if (document.location.toString().indexOf("/blog/post/") != -1)
        {
            $(".post .subtitle").append(
                $("<a/>").attr("href", "#").css("color", "#80BA47").css("fontWeight", "800").text("Редактировать").click(function(){
                    window.open("/admin/edit/" + document.location.toString().split("/").slice(3).join("/"), "", "toolbar=no,width=1024,height=768");
                    return false;
                })
            );
        }
    };

    if ($.cookie("admin"))
    {
        admin();
    }

    $(document).bind("keyup", "Shift+Return", function(){
        if ($.cookie("admin"))
        {
            $.cookie("admin", null);
            window.location.reload();
        }
        else
        {
            $.cookie("admin", "1");
            admin();
        }

        return false;
    });
});
