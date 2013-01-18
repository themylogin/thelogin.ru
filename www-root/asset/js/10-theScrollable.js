(function($){
    function Scrollable(scroller)
    {
        this.scroller = scroller;

        this.scrolledFrom = "top";
        this.scrolledAmount = 0;

        this.willPrepend = function()
        {
            if (this.scrolledFrom == "top")
            {
                this.scrolledFrom = "bottom";
                this.scrolledAmount = this.scroller.height() - this.scrolledAmount - this.scroller.visibleHeight();

                this.scroller.scrollBottom(this.scrolledAmount);
            }
        }

        this.willAppend = function()
        {
            if (this.scrolledFrom == "bottom")
            {
                this.scrolledFrom = "top";
                this.scrolledAmount = this.scroller.height() - this.scrolledAmount - this.scroller.visibleHeight();

                this.scroller.scrollTop(this.scrolledAmount);
            }
        }

        this.canScroll = function(px)
        {
            if (this.scrolledFrom == "top")
            {
                if (px > 0)
                {
                    var height = this.scroller.height();
                    var visibleHeight = this.scroller.visibleHeight();
                    if ((this.scrolledAmount + px) + visibleHeight <= height)
                    {
                        return px;
                    }
                    else
                    {
                        return height - visibleHeight - this.scrolledAmount;
                    }
                }

                if (px < 0)
                {
                    if (this.scrolledAmount + px >= 0)
                    {
                        return px;
                    }
                    else
                    {
                        return -this.scrolledAmount;
                    }
                }
            }

            if (this.scrolledFrom == "bottom")
            {
                if (px > 0)
                {
                    if (px <= this.scrolledAmount)
                    {
                        return px;
                    }
                    else
                    {
                        return this.scrolledAmount;
                    }
                }

                if (px < 0)
                {
                    var height = this.scroller.height();
                    var visibleHeight = this.scroller.visibleHeight();
                    if ((this.scrolledAmount + (-px)) + visibleHeight <= height)
                    {
                        return px;
                    }
                    else
                    {
                        return -(height - visibleHeight - this.scrolledAmount);
                    }
                }
            }

            return px;
        }

        this.scroll = function(px, animate)
        {
            if (this.scrolledFrom == "top")
            {
                this.scrolledAmount += px;
                this.scroller.scrollTop(this.scrolledAmount, animate);
            }
            if (this.scrolledFrom == "bottom")
            {
                this.scrolledAmount -= px;
                this.scroller.scrollBottom(this.scrolledAmount, animate);
            }
        }

        this.canSetHeight = function(newHeight)
        {
            if (this.scrolledFrom == "top")
            {
                return Math.min(newHeight, this.scroller.height() - this.scrolledAmount);
            }
            if (this.scrolledFrom == "bottom")
            {
                return Math.min(newHeight, this.scroller.visibleHeight() + this.scrolledAmount);
            }
        }

        this.height = function(val)
        {
            if (val == undefined)
            {
                return this.scroller.height();
            }
            else
            {
                if (this.scrolledFrom == "top")
                {
                    this.scroller.visibleHeight(val);
                }
                if (this.scrolledFrom == "bottom")
                {
                    this.scrolledAmount -= val - this.scroller.visibleHeight();
                    this.scroller.scrollBottom(this.scrolledAmount);
                    this.scroller.visibleHeight(val);
                }
            }
        }
    }

    function DivScroller($div)
    {
        this.$div = $div;
        this.$wrapper = $div.parent();

        this.scrollTop = function(px, animate)
        {
            this.$div.css("bottom", "auto");

            if (animate)
            {
                this.$div.animate({ top: -px }, animate);
            }
            else
            {
                this.$div.css("top", -px);
            }
        }

        this.scrollBottom = function(px, animate)
        {
            this.$div.css("top", "auto");

            if (animate)
            {
                this.$div.animate({ bottom: -px }, animate);
            }
            else
            {
                this.$div.css("bottom", -px);
            }
        }

        this.height = function(val)
        {
            return this.$div.height(val);
        }

        this.visibleHeight = function(val)
        {
            return this.$wrapper.height(val);
        }
    }

    function WindowScroller($window)
    {
        this.$window = $window;
        this.$document = $($window[0].document);

        this.scrollTop = function(px, animate)
        {
            if (animate)
            {
                this.$window.animate({ scrollTop : px }, animate);
            }
            else
            {
                this.$window.scrollTop(px);
            }
        }

        this.scrollBottom = function(px, animate)
        {
            console.log(px);

            var $this_window = this.$window;
            var $this_document = this.$document;

            // Высота страницы изменяется по мере загрузки элементов, а мы всё поддерживаем scrollTop
            var interval;
            var lastDocumentHeight = $this_document.height();
            var lastTimeDocumentHeightChanged = new Date().getTime();
            var lastSetScrollTop;
            var userScroll = 0;
            $this_window.on("scroll.theScrollable.WindowScroller", function(event){
                userScroll += lastSetScrollTop - $this_window.scrollTop();
            });
            interval = setInterval(function(){
                var documentHeight = $this_document.height();
                if (documentHeight != lastDocumentHeight)
                {
                    lastDocumentHeight = $this_document.height();
                    lastTimeDocumentHeightChanged = new Date().getTime();
                }
                else if (new Date().getTime() - lastTimeDocumentHeightChanged > 2000)
                {
                    $this_window.off("scroll.theScrollable.WindowScroller");
                    clearInterval(interval);
                }

                lastSetScrollTop = (documentHeight - $this_window.height()) - (px + userScroll);
                $this_window.scrollTop(lastSetScrollTop);
            }, 0);
        }

        this.height = function(val)
        {
            if (val == undefined)
            {
                return this.$document.height();
            }
            else
            {
                throw "Trying to set value of readonly property WindowScroller.height";
            }
        }

        this.visibleHeight = function(val)
        {
            if (val == undefined)
            {
                return this.$window.height();
            }
            else
            {
                throw "Trying to set value of readonly property WindowScroller.visibleHeight";
            }
        }
    }

    $.fn.theScrollable = function(){
        if (this[0] == window)
        {
            var that = this;
            var scrollable = new Scrollable(new WindowScroller(this));
            this.on("scroll.theScrollable.init", function(event){
                scrollable.scrolledFrom = "top";
                scrollable.scrolledAmount = that.scrollTop();
            });
            return scrollable;
        }
        else
        {
            return new Scrollable(new DivScroller(this));
        }
    };
})(jQuery);
