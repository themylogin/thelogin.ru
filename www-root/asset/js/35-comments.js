(function($){
    $.fn.extend({
        insertAtCaret: function(myValue, dontFocus){
            return this.each(function(i){
                if (document.selection)
                {
                    // IE
                    this.focus();
                    sel = document.selection.createRange();
                    sel.text = myValue;
                    if (dontFocus == undefined)
                        this.focus();
                }
                else if (this.selectionStart || this.selectionStart == "0")
                {
                    // FF, WebKit
                    var startPos = this.selectionStart;
                    var endPos = this.selectionEnd;
                    var scrollTop = this.scrollTop;
                    this.value = this.value.substring(0, startPos) + myValue + this.value.substring(endPos,this.value.length);
                    if (dontFocus == undefined)
                        this.focus();
                    this.selectionStart = startPos + myValue.length;
                    this.selectionEnd = startPos + myValue.length;
                    this.scrollTop = scrollTop;
                }
                else
                {
                    this.value += myValue;
                    if (dontFocus == undefined)
                        this.focus();
                }
            })
        },
        wrapAtCaret: function(open, close){
            return this.each(function(i){
                if (document.selection)
                {
                    // IE
                    this.focus();
                    sel = document.selection.createRange();
                    sel.text = open + sel.text + close;
                    this.focus();
                }
                else if (this.selectionStart || this.selectionStart == "0")
                {
                    // FF, WebKit
                    var startPos = this.selectionStart;
                    var endPos = this.selectionEnd;
                    var scrollTop = this.scrollTop;
                    this.value = this.value.substring(0, startPos) + open + this.value.substring(startPos, endPos) + close + this.value.substring(endPos,this.value.length);
                    this.focus();
                    this.selectionStart = startPos + (open.length + endPos - startPos + close.length);
                    this.selectionEnd = startPos + (open.length + endPos - startPos + close.length);
                    this.scrollTop = scrollTop;
                }
                else
                {
                    this.value += open + close;
                    this.focus();
                }
            })
        }
    });
})(jQuery);

$(function(){
    // Тэги
    $.each(["b", "i", "s", "u"], function(i, tag){
        $(".tag-helper-" + tag).click(function(){
            $(".comments-form textarea").wrapAtCaret("<" + tag + ">", "</" + tag + ">");
            return false;
        });
    });
    $(".tag-helper-a").click(function(){
        $(".comments-form textarea").wrapAtCaret("<a href=\"\">", "</a>");
        return false;
    });
    $(".tag-helper-img").click(function(){
        $(".comments-form textarea").wrapAtCaret("<img src=\"", "\" />");
        return false;
    });
    $(".tag-helper-pre").click(function(){
        $(".comments-form textarea").wrapAtCaret("<pre>", "</pre>");
        return false;
    });
    $(".tag-helper-quote").click(function(){
        $(".comments-form textarea").wrapAtCaret("<quote>", "</quote>");
        return false;
    });
    
    // Загрузка изображений
    $(".image-uploader").click(function(e){
        document.domain = "thelogin.ru";
        window.open("http://i.thelogin.ru/?from=thelogin.ru", "", "width=400,height=300,left=" + e.screenX + ",top=" + (e.screenY - 350) + ",scrollbars=yes,resizable=yes,toolbar=no,location=yes");
        return false;
    });
    
    // Цитата выделенного
    var quoteSelected = function(){
        var selectedText = "";
        if (window.getSelection)
        {
            selectedText = window.getSelection();
        }
        else if (document.getSelection)
        {
            selectedText = document.getSelection();
        }
        else if(document.selection)
        {
            selectedText = document.selection.createRange().text;
        }

        if (selectedText != "")
        {
            $(".comments-form.main textarea").insertAtCaret("<quote>" + selectedText + "</quote>\n", true);
        }

        return false;
    };
    $(document).bind("keydown", "Ctrl+Return", quoteSelected);
    $(".comment .quote-selected").live("click", function(){
        quoteSelected();
        return false;
    });
    $(".comment .quote-comment").live("click", function(){
        $(this).addClass("clicked");
        $(".comments-form.main textarea").insertAtCaret("<quote>" + $(this).parent().parent().find(".plaintext").text() + "</quote>\n", true);

        return false;
    });
    
    // Сохранение недописанных комментариев в localStorage
    if (typeof(localStorage) != "undefined")
    {
        $(".comments-form.main form").each(function(){
            var $form = $(this);
            var key = $form.attr("action");
            var $textarea = $form.find("textarea");
            
            $textarea.keyup(function(){
                try
                {
                    localStorage.setItem(key, $(this).val());
                }
                catch (e)
                {
                }
            });
            
            var text = localStorage.getItem(key);
            if (text)
            {
                $textarea.val(text);
            }
            
            $form.submit(function(){
                localStorage.removeItem(key);
            });
        });
    }

    // Отправка комментариев через AJAX
    $(".comments-form.main form").ajaxForm({
        beforeSubmit: function(arr, $form, options){
            $form.find("input").hide();
            $form.find("input").append("<img src='/css/loader.gif' style='display: block;' />");
        },
        dataType    : "html",
        success     : function(data){
            $(".comments-list").html($(data).find(".comments-list").html());
            $(".comments-form.main form").find("textarea").val("");
            $(".comments-form.main form").find("input").next().remove();
            $(".comments-form.main form").find("input").show();
        }
    });

    // Редактирование комментариев
    $(".comment .edit-comment").live("click", function(){
        var $comment = $(this).parent().parent();
        $comment.find(".text").html("<div class='comments-form' style='width: 99%;'><form action='/' method='post'><textarea name='text'>" + $comment.find(".plaintext").html() + "</textarea><input type='submit' value='Редактировать комментарий' /></form>");
        $comment.find("form").submit(function(){
            var text = $comment.find("textarea").val();
            $comment.find("input").replaceWith("<img src='/css/loader.gif' style='display: block;' />");
            $.post("/content/edit-comment/" + $comment.data("id") + "/", { "text" : text }, function(data){
                if (data.error)
                {
                    $comment.find("form img").replaceWith("<div style='color: #bf0303;'>" + data.error + "</div>");
                }
                else if (data.deleted)
                {
                    $comment.siblings(".comment:last").find(".edit-comment").show();
                    $comment.remove();

                    $(".comments-title:first").text("Комментарии (" + $(".comment").length + ")");
                }
                else
                {
                    $comment.find(".text").html(data.text);
                    $comment.find(".plaintext").text(text);
                }
            });
            return false;
        });
        
        return false;
    });
});
