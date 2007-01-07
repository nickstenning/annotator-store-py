/*
 * REST implementation of the connection to the annotation back-end
 */

// If this is true, uses paths like annotate/nnn
// if false, use paths like annotation/annotate.php?id=nnn
// rgrp: change this
ANNOTATION_NICE_URLS = true;

 /*
 * Initialize the REST annotation service
 */
function AnnotationService( wwwroot, user )
{
	this.wwwroot = wwwroot;
	this.username = user;
	return this;
}

/*
 * Fetch a list of annotations from the server
 */
AnnotationService.prototype.listAnnotations = function( url, f )
{
	// exclude content to lighten the size across the wire
	var serviceUrl;
	if ( ANNOTATION_NICE_URLS )
		serviceUrl = this.wwwroot + NICE_ANNOTATION_SERVICE_URL;
	else
		serviceUrl = this.wwwroot + UGLY_ANNOTATION_SERVICE_URL;
	serviceUrl += '?format=atom&exclude=content&user=' + encodeURIComponent( this.username ) + '&url=' + encodeURIComponent( url );
	
	if ( ANNOTATION_LOGUSER_URLS )
		serviceUrl += "&loguser=" + encodeURIComponent( this.username );
	
	var xmlhttp = createAjaxRequest( );
	xmlhttp.open( 'GET', serviceUrl );
	//xmlhttp.setRequestHeader( 'Accept', 'application/xml' );
	xmlhttp.onreadystatechange = function( ) {
		if ( xmlhttp.readyState == 4 ) {
			if ( xmlhttp.status == 200 ) {
				if ( null != f )
				{
					// alert( serviceUrl + "\n" + xmlhttp.responseText );
					f( xmlhttp.responseXML );
				}
			}
			else {
				trace( "ListAnnotations Server request failed with code " + xmlhttp.status + ":\n" + serviceUrl );
			}
			xmlhttp = null;
		}
	}
	trace( 'annotation-service', "AnnotationService.listAnnotations " + serviceUrl)
	xmlhttp.send( null );
}

/*
 * Create an annotation on the server
 * When successful, calls a function f with one parameter:  the URL of the created annotation
 */
AnnotationService.prototype.createAnnotation = function( annotation, f )
//url, offset, length, note, access, quote, quote_title, quote_author, f )
{
	var serviceUrl;
	if ( ANNOTATION_NICE_URLS )
		serviceUrl = this.wwwroot + NICE_ANNOTATION_SERVICE_URL;
	else
		serviceUrl = this.wwwroot + UGLY_ANNOTATION_SERVICE_URL;
		
	if ( ANNOTATION_LOGUSER_URLS )
		serviceUrl += "?loguser=" + encodeURIComponent( this.username );
	
	var body
		= 'url=' + encodeURIComponent( annotation.url )
		+ '&range=' + encodeURIComponent( annotation.range.toString( ) )
		+ '&note=' + encodeURIComponent( annotation.note )
		+ '&access=' + encodeURIComponent( annotation.access )
		+ '&quote=' + encodeURIComponent( annotation.quote )
		+ '&quote_title=' + encodeURIComponent( annotation.quote_title )
		+ '&quote_author=' + encodeURIComponent( annotation.quote_author )
	var xmlhttp = createAjaxRequest( );

	// rgrp hack as paste does not seem to support x-www-form-urlencoded
	serviceUrl += '?' + body 
	
	xmlhttp.open( 'POST', serviceUrl, true );
	xmlhttp.setRequestHeader( 'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8' );
	//xmlhttp.setRequestHeader( 'Accept', 'application/xml' );
	xmlhttp.setRequestHeader( 'Content-length', body.length );
	xmlhttp.onreadystatechange = function( ) {
		if ( xmlhttp.readyState == 4 ) {
			// No need for Safari hack, since Safari can't create annotations anyway.
			if ( xmlhttp.status == 201 ) {
				var url = xmlhttp.getResponseHeader( 'Location' );
				if ( null != f )
					f( url );
			}
			else {
				logError( "AnnotationService.createAnnotation failed with code " + xmlhttp.status + ":\n" + serviceUrl );
			}
			xmlhttp = null;
		}
	}
	trace( 'annotation-service', "AnnotationService.createAnnotation " + serviceUrl + "\nbody is:" + body );
	xmlhttp.send( body );
}

/*
 * Update an annotation on the server
 */
AnnotationService.prototype.updateAnnotation = function( annotation, f )
{
	var serviceUrl;
	if ( ANNOTATION_NICE_URLS )
		serviceUrl = this.wwwroot + NICE_ANNOTATION_SERVICE_URL + '/' + annotation.id;
	else
		serviceUrl = this.wwwroot + UGLY_ANNOTATION_SERVICE_URL + '?id=' + annotation.id;

	if ( ANNOTATION_LOGUSER_URLS )
		serviceUrl += ( ANNOTATION_NICE_URLS ? '?' : '&' ) + "loguser=" + encodeURIComponent( this.username );
	
	var body = '';
	if ( null != annotation.note )
		body = 'note=' + encodeURIComponent( annotation.note );
	if ( null != annotation.access )
		body += ( body == '' ? '' : '&' ) + 'access=' + annotation.access;
	
	// rgrp hack as paste does not seem to support x-www-form-urlencoded
	serviceUrl += '?' + body 

	var xmlhttp = createAjaxRequest( );
	xmlhttp.open( 'POST', serviceUrl, true );
	xmlhttp.setRequestHeader( 'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8' );
	//xmlhttp.setRequestHeader( 'Accept', 'application/xml' );
	xmlhttp.setRequestHeader( 'Content-length', body.length );
	xmlhttp.onreadystatechange = function( ) {
		if ( xmlhttp.readyState == 4 ) {
			// Safari is braindead here:  any status code other than 200 is converted to undefined
			// IE invents its own 1223 status code
			// See http://www.trachtenberg.com/blog/?p=74
			if ( 204 == xmlhttp.status || xmlhttp.status == null || xmlhttp.status == 1223 ) {
				if ( null != f )
					f( xmlhttp.responseXML );
			}
			else
				logError( "AnnotationService.updateAnnotation failed with code " + xmlhttp.status + " (" + xmlhttp.statusText + ")\n" + xmlhttp.statusText + "\n" + xmlhttp.responseText );
			xmlhttp = null;
		}
	}
	trace( 'annotation-service', "AnnotationService.updateAnnotation " + serviceUrl );
	trace( 'annotation-service', "  " + body );
	xmlhttp.send( body );
}

/*
 * Delete an annotation on the server
 */
AnnotationService.prototype.deleteAnnotation = function( annotationId, f )
{
	var serviceUrl;
	if ( ANNOTATION_NICE_URLS )
		serviceUrl = this.wwwroot + NICE_ANNOTATION_SERVICE_URL + '/' + annotationId;
	else
		serviceUrl = this.wwwroot + UGLY_ANNOTATION_SERVICE_URL + '?id=' + annotationId;

	if ( ANNOTATION_LOGUSER_URLS )
		serviceUrl += ( ANNOTATION_NICE_URLS ? '?' : '&' ) + "loguser=" + encodeURIComponent( this.username );
	
	var xmlhttp = createAjaxRequest( );
	xmlhttp.open( 'DELETE', serviceUrl, true );
	//xmlhttp.setRequestHeader( 'Accept', 'application/xml' );
	xmlhttp.onreadystatechange = function( ) {
		if ( xmlhttp.readyState == 4 ) {
			// Safari is braindead here:  any status code other than 200 is converted to undefined
			// IE invents its own 1223 status code
			if ( 204 == xmlhttp.status || xmlhttp.status == null || xmlhttp.status == 1223 ) {
				if ( null != f )
					f( xmlhttp.responseXML );
			}
			else
				logError( "AnnotationService.deleteAnnotation failed with code " + xmlhttp.status + "\n" + xmlhttp.responseText );
			xmlhttp = null;
		}
	}
	trace( 'annotation-service', "AnnotationService.deleteAnnotation " + serviceUrl );
	xmlhttp.send( null );
}

