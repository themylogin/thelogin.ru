$(function(){
    $.fn.extend({
    	adoptGallery	: function(){    		
			// var windowWidth = $(window).width();
			var windowWidth = $("#wrapper").width();

			/*
			var tuples = []; // [[imageWidth, margin, Math.abs(imageWidth / margin - 11)], ...]
			for (var imageWidth = 200; imageWidth <= 345; imageWidth++)
			{
				for (var margin = 10; margin <= 40; margin++)
				{
					var n = (windowWidth - margin) / (imageWidth + margin);
					if (n % 1 === 0)
					{
						tuples.push([imageWidth, margin, n == 5 ? 0 : Math.abs(imageWidth / margin - 11.5)]);
					}
				}
			}
			tuples = tuples.sort(function(tuple1, tuple2){
				return tuple1[2] < tuple2[2] ? -1 : 1;
			});
			*/

			// imageWidth = 11.5 * margin
			// (11.5 * margin + margin) * 5 = windowWidth;
			var tuples = [];
			var margin = Math.floor(windowWidth / 12.5 / 5);
			var imageWidth = Math.floor(11.5 * margin);
			for (var i = -2; i <= 2; i++)
			{
				for (var j = -2; j <= 2; j++)
				{
					var tryImageWidth = imageWidth + i;
					var tryMargin = margin + j;
					if (tryImageWidth * 5 + tryMargin * 6 <= windowWidth)
					{
						tuples.push([tryImageWidth, tryMargin]);
					}
				}
			}
			tuples = tuples.sort(function(tuple1, tuple2){
				var gap1 = windowWidth - (tuple1[0] * 5 + tuple1[1] * 6);
				var gap2 = windowWidth - (tuple2[0] * 5 + tuple2[1] * 6);
				return gap1 < gap2 ? -1 : 1;
			});

			if (tuples.length > 0)
			{
				imageWidth = tuples[0][0];
				imageHeight = Math.round(imageWidth / 4 * 3);
				margin = tuples[0][1];

				var $pageContent = $(".page-content");
				$pageContent.css("marginTop", margin);
				$pageContent.css("marginBottom", margin);
				$pageContent.css("marginLeft", margin);
				$("div.feed.gallery .content_item").each(function(){
					var $feedItem = $(this);

					$feedItem.css("marginRight", margin);
					$feedItem.css("marginBottom", margin);

					$feedItem.css("width", imageWidth);
					$feedItem.css("height", imageHeight);
					
					var $a = $feedItem.find("a");
					$a.css("width", imageWidth);
					$a.css("height", imageHeight);

					var $img = $a.find("img");
					var uncroppedThumbWidth, uncroppedThumbHeight;
		 			if ($img.data("width") / $img.data("height") > imageWidth / imageHeight)
		 			{
		 				uncroppedThumbWidth = Math.round(imageHeight * $img.data("width") / $img.data("height"));
		 				uncroppedThumbHeight = imageHeight;
		 			}
		 			else
		 			{
		 				uncroppedThumbWidth = imageWidth;
		 				uncroppedThumbHeight = Math.round(imageWidth * $img.data("height") / $img.data("width"));
		 			}
		 			if (Math.abs(uncroppedThumbWidth - imageWidth) < 10 && Math.abs(uncroppedThumbHeight - imageHeight) < 10)
		 			{
		 				uncroppedThumbWidth = imageWidth;
		 				uncroppedThumbHeight = imageHeight;
		 			}
		 			var cropLeft = Math.round((uncroppedThumbWidth - imageWidth) / 2);
		 			var cropTop = Math.round((uncroppedThumbHeight - imageHeight) / 2);
					$img.width(uncroppedThumbWidth);
					$img.height(uncroppedThumbHeight);
					$img.css("left", "-" + cropLeft + "px");
					$img.css("top", "-" + cropTop + "px");
				});
			}
    	}
	});

	$().adoptGallery();
    $(window).bind("resize.gallery", $().adoptGallery);
    $(window).bind("theContentLoaded.gallery", $().adoptGallery);
});
