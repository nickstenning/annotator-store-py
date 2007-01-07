/*
 * Languages for annotation Javascript
 */

/*
 * Fetch a localized string
 * This is a function so that it can be replaced with another source of strings if desired
 * (e.g. in a database).  The application uses short English-language strings as keys, so
 * that if the language source is lacking the key can be returned instead.
 */
function getLocalized( s )
{
	return LocalizedAnnotationStrings[ s ];
}

LocalizedAnnotationStrings = {
	'lang' : 'en',
	
	// Button titles
	'public annotation' : 'This annotation is public.',
	'private annotation' : 'This annotation is private.',	
	'delete annotation button' : 'Delete this annotation.',
	
	// Errors
	'browser support of W3C range required for annotation creation' :
		'Your browser does not support the W3C range standard, so you cannot create annotations.',
	'select text to annotate' : 'You must select some text to annotate.',
	'invalid selection' : 'Selection range is not valid.',
	'corrupt XML from service' : 'An attempt to retrieve annotations from the server returned corrupt XML data.' 
};

