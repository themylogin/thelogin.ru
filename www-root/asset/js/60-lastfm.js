$(function(){
    $(".lastfm-chart").each(function(){
        var $chart = $(this);

        $chart.find("ul").on("click", "li", function(){
            var $li = $(this);
            var $all = $(this).parent().find("li");

            $all.removeClass("current");
            $li.addClass("current");

            $chart.find("table").hide();
            $chart.find("table:nth-child(" + ($all.index($li) + 1) + ")").show();
        });
    });
});
