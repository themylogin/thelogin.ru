(function($){
    var methods = {
        init: function(options){
            return this.each(function(){
                var settings = $.extend({
                    "feed"          : "",
                    "updateTimeout" : 60000,
                }, options);

                $(this).data("theContentLoader", settings);
                $(this).data("theContentLoader_nothingUpAt", 0);
                $(this).data("theContentLoader_nothingDownAt", 0);
            });
        },

        loadUp: function(count, eventHandlers){
            var $contentArea = $(this);
            var settings = $(this).data("theContentLoader");

            var query = {
                "count" : count,
                "after" : $contentArea.is(":parent") ? $contentArea.find(">:first").data("createdAt") : undefined,
            };
            var newEventHandlers = $.extend({
                "load"          : undefined,
                "contentItem"   : function(contentItem){
                    $contentArea.prepend(contentItem);
                },
                "ready"         : undefined,
            }, eventHandlers);
            return $(this).theContentLoader("_load", "theContentLoader_nothingUpAt", query, newEventHandlers);
        },
        loadDown: function(count, eventHandlers){
            var $contentArea = $(this);
            var settings = $(this).data("theContentLoader");

            var query = {
                "count" : count,
                "before": $contentArea.is(":parent") ? $contentArea.find(">:last").data("createdAt") : $contentArea.data("start"),
            };
            var newEventHandlers = $.extend({
                "load"          : undefined,
                "contentItem"   : function(contentItem){
                    $contentArea.append(contentItem);
                },
                "ready"         : undefined,
            }, eventHandlers);
            return $(this).theContentLoader("_load", "theContentLoader_nothingDownAt", query, newEventHandlers);
        },
        _load: function(timeoutKey, query, eventHandlers){
            var $contentArea = $(this);
            var settings = $(this).data("theContentLoader");

            if (new Date().getTime() < $(this).data(timeoutKey) + settings["updateTimeout"])
            {
                return false;
            }

            if ($contentArea.hasClass("loading"))
            {
                return true;
            }

            $contentArea.addClass("loading");
            $.ajax({
                url     :   (settings["feed"] == "index" ? "" : "/" + settings["feed"]) + "/json/",
                data    :   query,
                dataType:   "json",
                success :   function(contentItems)
                {
                    if (!contentItems.length)
                    {
                        $contentArea.data(timeoutKey, new Date().getTime());
                    }

                    if (eventHandlers["load"])
                    {
                        eventHandlers["load"]();
                    }
                    $.each(contentItems, function(i, contentItem){
                        if (eventHandlers["contentItem"])
                        {
                            eventHandlers["contentItem"](contentItem);
                        }
                    });
                    if (eventHandlers["ready"])
                    {
                        eventHandlers["ready"]();
                    }

                    $contentArea.removeClass("loading");
                    $(window).trigger("theContentLoaded");
                },
                error   :   function()
                {
                    $contentArea.removeClass("loading");
                }
            });
            return true;
        },
    };

    $.fn.theContentLoader = function(method){
        if (!method || typeof method === "object")
        {
            return methods.init.apply(this, arguments);
        }
        if (methods[method])
        {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        }
    };
})(jQuery);
