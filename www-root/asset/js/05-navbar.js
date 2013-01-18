$(function(){
    $authorization = $(".navbar .authorization.authorized");
    if ($authorization.length)
    {
        $authorization.find("a").click(function(event){
            event.stopPropagation();
        });
        $authorization.click(function(){
            $(this).toggleClass("clicked");
        });
        $(document).click(function(event){
            if (!$(event.target).closest($authorization.selector).length)
            {
                $authorization.removeClass("clicked");
            }
        });
    }
});
