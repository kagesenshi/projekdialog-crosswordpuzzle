(function($) {
	$(function() {
		// provide crossword entries in an array of objects like the following example
		// Position refers to the numerical order of an entry. Each position can have 
		// two entries: an across entry and a down entry
        var jsonurl = $('#puzzle-wrapper').attr('data-crossword-url');
        $.get(jsonurl, function (data) {	
    		$('#puzzle-wrapper').crossword(data);
        }, 'json');
		
	})
	
})(jQuery)
