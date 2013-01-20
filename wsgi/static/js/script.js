(function($) {
	$(function() {
		// provide crossword entries in an array of objects like the following example
		// Position refers to the numerical order of an entry. Each position can have 
		// two entries: an across entry and a down entry
        $.get('puzzle.json', function (data) {	
    		$('#puzzle-wrapper').crossword(data);
        }, 'json');
		
	})
	
})(jQuery)
