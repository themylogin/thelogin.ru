$(window).load(function(){
    var $mainCol = $(".main-col-wrapper");
    var $rightCol = $(".right-col-wrapper");
    var $lastfm = $rightCol.find(".block:has(.lastfm:has(.artist-wrapper))");

    if ($lastfm.length)
    {
    	if ($rightCol.height() + $rightCol.width() > $mainCol.height())
    	{
    		$mainCol.append($lastfm);
    	}
    }
});
 
