$(function(){
    $.fn.extend({
        // Прокрутить tinyscrollbar({ axis : "x" })
        tinyscrollbar_scrollTo: function(pxLeft){
            return this.each(function(){
                var $this = $(this);
                var $thumb = $this.find(".thumb");
                $this.tinyscrollbar_update(Math.min(Math.max(0, (pxLeft - $thumb.width() / 2) / (1 + $thumb.width() / $this.width())), $this.find(".overview").width() - $this.width()));

                var $marker = $this.find(".marker");
                $marker.css("display", "block");
                $marker.css("left", pxLeft + "px");
            });
        }
    });

    if (!$("body").hasClass("feed"))
    {
        return;
    }

    var $window = $(window);
    var $document = $(document);
    var $feed = $("div.feed:first");
    $feed.theContentLoader({ "feed" : $feed.data("feed")}); // Загрузчик для контента
    var scrollable = $window.theScrollable();               // Прокрутчик для окна

    var $pagination = $(".pagination");
    $pagination.css("position", "fixed");
    $pagination.css("bottom", "-" + $pagination.height() + "px");
    $pagination.after($("<div/>").css("height", $pagination.height() + "px"));
    $pagination.tinyscrollbar({ axis : "x"});

    $window.on("scroll.feedInfiniteScroll", function(){
        if ($window.scrollTop() > 0)
        {
            $pagination.stop();
            $pagination.animate({ bottom: 0 });
        }
        else
        {
            $pagination.stop();
            $pagination.animate({ bottom: -$pagination.height() });
        }

        if ($window.scrollTop() + $window.height() + 300 > $document.height())
        {
            $feed.theContentLoader("loadDown", 10, {
                "load"  : function(){
                    scrollable.willAppend();
                },
            });
        }

        var skippedFeedItems = 0;
        $feed.find(">*").each(function(i){
            if ($(this).offset().top > $window.scrollTop())
            {
                $pagination.tinyscrollbar_scrollTo(Math.round($pagination.data("itemWidth") * (skippedFeedItems + i)));
                return false;
            }
        });
    });
});
