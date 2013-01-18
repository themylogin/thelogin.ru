$(function(){
    $(".social .share.facebook").live("click", function(){
        window.open("http://www.facebook.com/sharer/sharer.php?t=" + encodeURIComponent($(this).data("title")) + "&u=" + encodeURIComponent($(this).data("url")) + "&src=sp", "facebook-share", "width=640,height=440,scrollbars=yes,resizable=yes,toolbar=no,location=yes");
        
        return false;
    });
    
    $(".social .share.vkontakte").live("click", function(){
        window.open("http://vkontakte.ru/share.php?title=" + encodeURIComponent($(this).data("title")) + "&url=" + encodeURIComponent($(this).data("url")), "vkontakte-share", "width=550,height=380,scrollbars=yes,resizable=yes,toolbar=no,location=yes");
        
        return false;
    });
    
    $(".social .share.twitter").live("click", function(){
        window.open("//twitter.com/intent/tweet?original_referer=http%3A%2F%2Fnew.thelogin.ru%2F&source=tweetbutton&text=" + encodeURIComponent($(this).data("title")) + "&url=" + encodeURIComponent($(this).data("url")) + "&via=themylogin", "twitter-share", "width=550,height=520,scrollbars=yes,resizable=yes,toolbar=no,location=yes");

        return false;
    });
});
