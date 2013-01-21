$(function(){    
    var minHeight = 117;        // Минимальная высота timeline (твит из трёх строчек)
    var minEventHeight = 60;    // Минимальная высота события (твит из одной строчки)

    var $mainCol    = $(".main-col-wrapper");       // Колонка с контентом, под неё будем погонять высоту таймлайна
    var $rightCol   = $(".right-col-wrapper");      // Колонка с таймлайном
    var $timeline   = $rightCol.find(".timeline");  // Таймлайн
    var $events     = $timeline.find(".events");    // События в таймлайне

    // Если на странице нет таймлайна, ничего делать не нужно
    if (!$timeline.length)
    {
        return;
    }

    $events.theContentLoader({ "feed" : "timeline"});   // Загрузчик для событий
    var scrollable = $events.theScrollable();           // Прокрутчик для событий

    /**
     * Сделать timeline во всю высоту страницы
     */
    function adjustHeight()
    {
        // Размер колонки с таймлайном должен быть точно равен размеру колонки с контентом
        if ($rightCol.height() != $mainCol.height())
        {
            var newHeight = Math.max(
                $timeline.outerHeight() + ($mainCol.height() - $rightCol.height()), // Увеличим (или уменьшим) на разницу высот
                minHeight                                                           // Но меньше определённой нельзя
            );
            var newAvailableHeight = scrollable.canSetHeight(newHeight);
            if (newAvailableHeight == newHeight)
            {
                scrollable.height(newHeight);
            }
            else
            {
                $events.theContentLoader("loadDown",
                    Math.ceil((newHeight - newAvailableHeight) / minEventHeight),   // Столько событий не хватает
                    {
                        "load"  : function(){
                            scrollable.willAppend();
                        },
                        "ready" : function(){
                            var newAvailableHeight = scrollable.canSetHeight(newHeight);
                            scrollable.height(newAvailableHeight);

                            if (newAvailableHeight != newHeight)
                            {
                                nothingDownAt = new Date().getTime();
                            }
                        },
                    }
                );
            }
        }
    }
    $(window).on("load.timeline.adjustHeight", adjustHeight);
    $(window).on("ready.timeline.adjustHeight", adjustHeight);
    $(window).on("scroll.timeline.adjustHeight", adjustHeight);
    $(window).on("theContentLoaded.timeline.adjustHeight", adjustHeight);   // custom event fired from theContentLoader

    /**
     * Прокрутить timeline
     */
    function scroll(px, animate)
    {
        var availablePx = scrollable.canScroll(px);
        if (availablePx == px)
        {
            scrollable.scroll(px, animate);
            return true;
        }
        else
        {
            if (px > 0)
            {
                return $events.theContentLoader("loadDown", 100, {
                    "load"  : function(){
                        scrollable.willAppend();
                    },
                    "ready" : function(){
                        var availablePx = scrollable.canScroll(px);
                        scrollable.scroll(availablePx, animate);
                    }
                });
            }
            else
            {
                return $events.theContentLoader("loadUp", 100, {
                    "load"  : function(){
                        scrollable.willPrepend();
                    },
                    "ready" : function(){
                        var availablePx = scrollable.canScroll(px);
                        scrollable.scroll(availablePx, animate); 
                    }
                });
            }
        }
    }
    // Колесо мыши по таймлайну
    $timeline.on("mousewheel", function(event, delta, deltaX, deltaY){
        return !scroll(-deltaY * minHeight, false);  // Удалось прокрутить - не передаём событие странице
    });
    // Стрелочки прокрутки
    $timeline.find(".scroll-button.up").click(function(){
        return !scroll(-2 * minHeight, true);    // Удалось прокрутить - не передаём событие странице
    });
    $timeline.find(".scroll-button.down").click(function(){
        return !scroll(2 * minHeight, true);   // Удалось прокрутить - не передаём событие странице
    });
});
