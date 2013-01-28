$(function(){
    $.fn.extend({
        handle_flowplayers: function(){
            $("a.flowplayer-audio:not(:has(object))").flowplayer("/asset/js/flowplayer-3.2.7.swf", {
                clip: {
                    autoPlay: false
                },
                plugins: {
                    controls: {
                        autoHide: false,
                        fullscreen: false,
                        height: 30,

                        buttonColor: 'rgba(0, 0, 0, 0.9)',
                        buttonOverColor: '#000000',
                        backgroundColor: '#D7D7D7',
                        backgroundGradient: 'medium',
                        sliderColor: '#FFFFFF',

                        sliderBorder: '1px solid #808080',
                        volumeSliderColor: '#FFFFFF',
                        volumeBorder: '1px solid #808080',

                        timeColor: '#000000',
                        durationColor: '#535353'
                    }
                }
            });
            
            $("a.flowplayer-video:not(:has(object))").flowplayer("/asset/js/flowplayer-3.2.7.swf", {
                clip: {
                    autoPlay: false,
                    scaling: 'fit'
                },
                plugins: {
                    controls: {
                        autoHide: false,
                        height: 30,
               
                        buttonColor: 'rgba(0, 0, 0, 0.9)',
                        buttonOverColor: '#000000',
                        backgroundColor: '#D7D7D7',
                        backgroundGradient: 'medium',
                        sliderColor: '#FFFFFF',

                        sliderBorder: '1px solid #808080',
                        volumeSliderColor: '#FFFFFF',
                        volumeBorder: '1px solid #808080',

                        timeColor: '#000000',
                        durationColor: '#535353'
                    }
                }
            });

            return this;
        }
    });

    $().handle_flowplayers(); // С первого раза не сработает
    $().handle_flowplayers();
    $(window).bind("theContentLoaded.flowplayer", function(){
        $().handle_flowplayers();
        $().handle_flowplayers();
    });
});
