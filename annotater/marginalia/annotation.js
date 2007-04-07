/*
 * annotation.js
 *
 * Web Annotation is being developed for Moodle with funding from BC Campus 
 * and support from Simon Fraser University and SFU's Applied Communication
 * Technologies Group and the e-Learning Innovation Centre of the
 * Learning Instructional Development Centre at SFU
 * Copyright (C) 2005 Geoffrey Glass www.geof.net
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 */

// namespaces
NS_PTR = 'http://www.geof.net/code/annotation/';
NS_ATOM = 'http://www.w3.org/2005/Atom';

// The names of HTML/CSS classes used by the annotation code.
AN_NOTES_CLASS = 'notes';			// the notes portion of a fragment
AN_HIGHLIGHT_CLASS = 'annotation';// class given to em nodes for highlighting
AN_HOVER_CLASS = 'hover';			// assigned to highlights and notes when the mouse is over the other
AN_ANNOTATED_CLASS = 'annotated';	// class added to fragment when annotation is on
AN_SELFANNOTATED_CLASS = 'self-annotated';  // annotations are by the current user (and therefore editable)
AN_DUMMY_CLASS = 'dummy';			// used for dummy item in note list
AN_RANGEMISMATCH_ERROR_CLASS = 'annotation-range-mismatch';	// one or more annotations don't match the current state of the document
AN_ID_PREFIX = 'a';					// prefix for annotation IDs in element classes and IDs
AN_SUN_SYMBOL = '\u25cb'; //'\u263c';
AN_MOON_SYMBOL = '\u25c6'; //'\u2641';

// Length limits
MAX_QUOTE_LENGTH = 1000;
MAX_NOTE_LENGTH = 250;

/*
 * Must be called before any other annotation functions
 * wwwroot - the root of the annotation service
 * anuser - the user whose annotations are to be shown
 * thisuser - the current user (may differ from anuser)
 * urlBase - if null, annotation URLs are used as normal.  Otherwise, they are searched for this
 * string and anything preceeding it is chopped off.  This is necessary because IE lies about
 * hrefs:  it provides an absolute URL for that attribute, rather than the actual text.  In some
 * cases, absolute URLs aren't desirable (e.g. because the annotated resources might be moved
 * to another host, in which case the URLs would all break).
 */
function annotationInit( wwwroot, thisuser, anuser, urlBase )
{
	window.annotationUrlBase = urlBase;
	window.annotationService = new AnnotationService( wwwroot, anuser );
	window.annotationThisUser = thisuser;

	// Event handlers
	if ( document.addEventListener )
		document.addEventListener( 'keyup', _keyupCreateAnnotation, false );
	else  // for IE:
	{
		if ( document.onkeyup )
			document.onkeyup = function( event ) { _keyupCreateAnnotation(event); document.onkeyup; }
		else
			document.onkeyup = _keyupCreateAnnotation;
	}
}

/*
 * Get the list of notes.  It is a DOM element containing children,
 * each of which has an annotation field referencing an annotation.
 * There is a dummy first child because of spacing problems in IE.
 */
PostMicro.prototype.getNotesElement = function( )
{
	// Make sure it has the additional annotation properties added
	if ( ! this.notesElement )
	{
		var t = getChildByTagClass( this.element, null, AN_NOTES_CLASS, _skipPostContent );
		this.notesElement = t.getElementsByTagName( 'ol' )[ 0 ];
	}
	return this.notesElement;
}


/*
 * Parse Atom containing annotation info and return an array of annotation objects
 */
function parseAnnotationXml( xmlDoc )
{
	var annotations = new Array( );
	
	if ( xmlDoc.documentElement.tagName == "error" )
	{
		logError( "parseAnnotationXML Error: " + xmlDoc.documentElement.textValue() );
		alert( getLocalized( 'corrupt XML from service' ) );
		return null;
	}
	else
	{
		for ( var i = 0;  i < xmlDoc.documentElement.childNodes.length;  ++i ) {
			try {
				child = xmlDoc.documentElement.childNodes[ i ];
				// obliged to use tagName here rather than localName due to IE
				if ( child.namespaceURI == NS_ATOM && getLocalName( child ) == 'entry' )
				{
					var hOffset, hLength, text, url, id;
					var annotation = new Annotation( );
					var rangeStr = null;
					for ( var field = child.firstChild;  field != null;  field = field.nextSibling )
					{
						if ( field.namespaceURI == NS_ATOM && getLocalName( field ) == 'link' )
						{
							var rel = field.getAttribute( 'rel' );
							var href = field.getAttribute( 'href' );
							// What is the role of this link element?  (there are several links in each entry)
							if ( 'self' == rel )
								annotation.id = href.substring( href.lastIndexOf( '/' ) + 1 );
							else if ( 'related' == rel )
							{
								if ( null != window.annotationUrlBase
									&& href.substring( 0, window.annotationUrlBase.length ) == window.annotationUrlBase )
								{
									href = href.substring( window.annotationUrlBase.length );
								}
								annotation.post = findPostByUrl( href );
							}
						}
						else if ( NS_ATOM == field.namespaceURI && 'author' == getLocalName( field ) )
						{
							for ( var nameElement = field.firstChild;  null != nameElement;  nameElement = nameElement.nextSibling )
							{
								if ( NS_ATOM == nameElement.namespaceURI && 'name' == getLocalName( nameElement ) )
									annotation.userid = nameElement.firstChild ? nameElement.firstChild.nodeValue : null;
							}
						}
						else if ( field.namespaceURI == NS_ATOM && getLocalName( field ) == 'title' )
							annotation.note = null == field.firstChild ? '' : field.firstChild.nodeValue;
						else if ( field.namespaceURI == NS_ATOM && getLocalName( field ) == 'summary' )
							annotation.quote = null == field.firstChild ? null : field.firstChild.nodeValue;
						else if ( field.namespaceURI == NS_PTR && getLocalName( field ) == 'range' )
							rangeStr = field.firstChild.nodeValue;
						else if ( field.namespaceURI == NS_PTR && getLocalName( field ) == 'access' )
						{
							if ( field.firstChild )
								annotation.access = field.firstChild.nodeValue;
							else
								annotation.access = 'private';
						}
					}
					// This should really check the validity of the whole annotation.  Most important
					// though is that the ID not be zero, otherwise this would interfere with the
					// creation of new annotations.
					if ( 0 != annotation.id && null != annotation.post )
					{
						annotation.range = new WordRange( );
						annotation.range.fromString( rangeStr, annotation.post.contentElement );
						annotations[ annotations.length ] = annotation;
					}
				}
			} catch(e) {
				trace( 'annotation-service', "annotation.parseAnnotationXml" + e.name + " " + e.message );
			}
		}
		annotations.sort( compareAnnotationRanges );
		return annotations;
	}
}


/* ************************ Add/Show Functions ************************ */
/* These are for adding an annotation to the post and display.
 * addAnnotation calls the other three in order:
 * showNote, highlightRange, positionNote
 * None of these do anything with the server, but they do create interface
 * elements which when activated call server functions.
 *
 * In order to achieve a single point of truth, the only annotation list
 * is the list of annotation notes attached to each post in the DOM.
 * On the one hand, the two can't vary independently.  But I can't think
 * why they would need to.  This way, they can't get out of sync.
 */

/*
 * Get the index where an annotation is or where it would display
 */
PostMicro.prototype.getAnnotationIndex = function( annotation )
{
	var notesElement = this.getNotesElement( );
	// Go from last to first, on the assumption that this function will be called repeatedly
	// in order.  Calling in reverse order gives worst-case scenario O(n^2) behavior.
	// Don't forget the first node in the list is a dummy with no annotation.
	var pos = notesElement.childNodes.length;
	for ( var note = notesElement.lastChild;  null != note;  note = note.previousSibling )
	{
		--pos;
		if ( null != note.annotation )
		{
			if ( note.annotation.id == annotation.id )
				return pos;
			else if ( compareAnnotationRanges( note.annotation, annotation ) < 0 )
				break;
		}
	}
	return pos;
}

/*
 * Add an annotation to the local annotation list and display.
 */
PostMicro.prototype.addAnnotation = function( annotation )
{
	var pos = this.getAnnotationIndex( annotation );
	if ( ! this.showHighlight( annotation ) )
		return -1;
	this.showNote( pos, annotation );
	return pos;
}

/*
 * Create an item in the notes list
 * pos - the position in the list
 * annotation - the annotation
 */
PostMicro.prototype.showNote = function( pos, annotation )
{
	var noteList = this.getNotesElement();

	// Ensure we have a dummy first sibling
	if ( null == noteList.firstChild )
	{
		var dummy = document.createElement( 'li' );
		dummy.setAttribute( 'class', AN_DUMMY_CLASS );
		noteList.appendChild( dummy );
	}
	
	// Find the notes that will precede and follow this one
	var prevNode = noteList.firstChild; // the dummy first node
	var nextNode = noteList.firstChild.nextSibling; // skip dummy first node
	for ( var j = 0;  j < pos && null != nextNode;  ++j )
	{
		prevNode = nextNode;
		nextNode = nextNode.nextSibling;
	}

	// Create the list item
	var postMicro = this;
	var noteElement = document.createElement( 'li' );
	noteElement.id = AN_ID_PREFIX + annotation.id;
	noteElement.annotationId = annotation.id;
	noteElement.annotation = annotation;
	
	// Create its contents
	if ( annotation.isEditing )
	{
		// Create the edit box
		var editNode = document.createElement( "textarea" );
		editNode.rows = 3;
		editNode.appendChild( document.createTextNode( annotation.note ) );
		noteElement.appendChild( editNode );
		// Set focus after making visible later (IE requirement; it would be OK to do it here for Gecko)
		//editNode.onkeyup = function( event ) { event = getEvent( event ); return postMicro.editKeyUp( event, this ); };
		editNode.annotationId = annotation.id;
		editNode.onkeypress = _editKeyDown;
		editNode.onblur = _saveAnnotation;
	}
	else
	{
		if ( annotation.userid == window.annotationThisUser )
		{
			// add the delete button
			var buttonNode = document.createElement( "button" );
			buttonNode.setAttribute( 'type', "button" );
			buttonNode.className = 'annotation-delete';
			buttonNode.setAttribute( 'title', getLocalized( 'delete annotation button' ) );
			buttonNode.appendChild( document.createTextNode( "x" ) );
			buttonNode.annotationId = annotation.id;
			buttonNode.onclick = _deleteAnnotation;
			noteElement.appendChild( buttonNode );
			/* access button removed because of new access values and haven't come
			 * up with a clear user interface to choosing among them
			// add the access button
			buttonNode = document.createElement( "button" );
			buttonNode.type = "button";
			buttonNode.className = 'annotation-access';
			buttonNode.setAttribute( 'title', annotation.access == 'public' ?
				getLocalized( 'public annotation' ) : getLocalized( 'private annotation' ) );
			buttonNode.appendChild( document.createTextNode( annotation.access == 'public' ? AN_SUN_SYMBOL : AN_MOON_SYMBOL ) );
			buttonNode.annotation = annotation;
			buttonNode.onclick = _toggleAnnotationAccess;
			noteElement.appendChild( buttonNode );
			*/
			// Add edit and hover behaviors
			noteElement.onmouseover = _hoverAnnotation;
			noteElement.onmouseout = _unhoverAnnotation;
			noteElement.onclick = _editAnnotation;
		}
		// add the text content
		noteElement.appendChild( document.createTextNode( annotation.note ) );
	}

	var highlightElement = getChildByTagClass( this.contentElement, 'em', AN_ID_PREFIX + annotation.id, null );
	noteElement.style.marginTop = '' + this.calculateNotePushdown( prevNode, highlightElement ) + 'px';
	
	// Insert the note in the list
	noteList.insertBefore( noteElement, nextNode );
	
	return noteElement;
}

/*
 * Display a single highlighted range
 * Inserts em tags of class annotation were appropriate
 */
PostMicro.prototype.showHighlight = function( annotation )
{
	var textRange = wordRangeToTextRange( annotation.range, annotation.post.contentElement, _skipSmartcopy );
	// Check whether the content of the text range matches what the annotation expects
	if ( null == textRange )
	{
		trace( 'find-quote', 'Annotation ' + annotation.id + ' not within the content area.' );
		return false;
	}
	var actual = getTextRangeContent( textRange, _skipSmartcopy );
	var quote = annotation.quote;
	actual = actual.replace( /\s|\u00a0\s*/g, ' ' );
	quote = quote.replace( /\s|\u00a0\s*/g, ' ' );
	// commented out by rgrp
	// if ( actual != quote )
	// {
	//	trace( 'find-quote', 'Annotation ' + annotation.id + ' range \"' + actual + '\" doesn\'t match "' + quote + '"' );
	//	return false;
	// }
	var nrange = NormalizedRange( textRange, this.contentElement, _skipSmartcopy );
	this.showHighlight_Recurse( annotation, this.contentElement, nrange, 0 );
	trace( 'find-quote', 'Annotation ' + annotation.id + ' range found.' );
	return true;
}

PostMicro.prototype.showHighlight_Recurse = function( annotation, node, textRange, position )
{
	var start = textRange.offset;
	var end = textRange.offset + textRange.length;

	// if we've completed all our markup, finish
	if ( position > end )
		return 0;		// what a hack!  usually returns the length, but this time returns a node!
	
	if ( node.nodeType == ELEMENT_NODE )
	{
		if ( hasClass( node, 'smart-copy' ) )
			return 0;	// don't include temporary smartcopy content in count
		else
		{
			var children = new Array();
			var length = 0;
			for ( var i = 0;  i < node.childNodes.length;  ++i )
				children[ i ] = node.childNodes[ i ];
			for ( var i = 0;  i < children.length;  ++i )
				length += this.showHighlight_Recurse( annotation, children[ i ], textRange, position + length );
			return length;
		}
	}
	else if ( node.nodeType == TEXT_NODE || node.nodeType == CDATA_SECTION_NODE )
	{
		var length = node.length;
		var newNode;
		if ( start < position + length )
		{
			// Is <em> valid in this position in the document?  (It might well not be if
			// this is a script or style element, or if this is whitespace text in
			// certain other nodes (ul, ol, table, tr, etc.))
			if ( isValidHtmlContent( node.parentNode.tagName, 'em' ) )
			{
				var a = start < position ? 0 : start - position;
				var b = end > position + length ? length : end - position;
				var text = node.nodeValue + "";
				// break the portion of the node before the annotation off and insert it
				if ( a > 0 )
				{
					newNode = document.createTextNode( text.substring( 0, a ) );
					node.parentNode.insertBefore( newNode, node );
				}
				// replace node content with annotation
				newNode = document.createElement( 'em' );
				newNode.className = AN_HIGHLIGHT_CLASS + ' ' + AN_ID_PREFIX + annotation.id;
				newNode.onmouseover = _hoverAnnotation;
				newNode.onmouseout = _unhoverAnnotation;
				newNode.annotation = annotation;
				node.parentNode.replaceChild( newNode, node );
				newNode.appendChild( node );
				node.nodeValue = text.substring( a, b );
				node = newNode;	// necessary for the next bit to work right
				// break the portion of the node after the annotation off and insert it
				if ( b < length )
				{
					newNode = document.createTextNode( text.substring( b ) );
					if ( node.nextSibling )
						node.parentNode.insertBefore( newNode, node.nextSibling );
					else
						node.parentNode.appendChild( newNode );
				}
			}
		}
		else
		{
			trace( 'highlighting', "Don't draw <em> within <" + node.parentNode.tagName + ">: " + node.nodeValue );
		}
		return length;
	}
	else
		return 0;
}

/*
 * Position the notes for an annotation next to the highlight
 * It is not necessary to call this method when creating notes, only when the positions of
 * existing notes are changing
 */
PostMicro.prototype.positionNote = function( annotation )
{
	var note = document.getElementById( AN_ID_PREFIX + annotation.id );
	while ( null != note )
	{
		var highlight = getChildByTagClass( this.contentElement, 'em', AN_ID_PREFIX + annotation.id, null );
		if ( null == highlight || null == note )
			logError( "positionNote:  Couldn't find note or highlight for " + AN_ID_PREFIX + annotation.id );
		else
			note.style.marginTop = '' + this.calculateNotePushdown( note.previousSibling, highlight );
		note = note.nextSibling;
	}
}

/*
 * Calculate the pixel offset from the previous displayed note to this one
 * by setting the top margin to the appropriate number of pixels.
 * The previous note and the highlight must already be displayed, but this note
 * does not yet need to be part of the DOM.
 */
PostMicro.prototype.calculateNotePushdown = function( previousNoteElement, highlightElement )
{
	var noteY = getElementYOffset( previousNoteElement, null ) + previousNoteElement.offsetHeight;
	var highlightY = getElementYOffset( highlightElement, null );
	highlightElement.border = 'red 1px solid';
	trace( 'align-notes', 'calculateNotePushdown for ' + getNodeText( highlightElement ) + ' (' + highlightElement.className + ') : highlightY=' + highlightY + ', noteY=' + noteY );
	return ( noteY < highlightY ) ? highlightY - noteY : 0;
}

/*
 * Reposition notes, starting with the note list element passed in
 */
PostMicro.prototype.repositionNotes = function( element )
{
	// We don't want the browser to scroll, which it might under some circumstances
	// (I believe it's a timing thing)
	for ( ;  null != element;  element = element.nextSibling )
	{
		var highlightElement = getChildByTagClass( this.contentElement, null, AN_ID_PREFIX + element.annotation.id, null );
		element.style.marginTop = '' + this.calculateNotePushdown( element.previousSibling, highlightElement ) + 'px';
	}
}

/* ************************ Remove/Hide Functions ************************ */
/* These are counterparts to the add/show functions above */

/*
 * Remove all annotations from a post
 * Returns an array of removed annotations so the caller can destruct them if necessary
 */
PostMicro.prototype.removeAnnotations = function( )
{
	var notesElement = this.getNotesElement( );
	var child = notesElement.firstChild;
	var annotations = new Array( );
	while ( null != child )
	{
		if ( child.annotation )
		{
			annotations[ annotations.length ] = child.annotation;
			child.annotation = null;
		}
		notesElement.removeChild( child );
		child = notesElement.firstChild;
	}
	stripMarkup( this.contentElement, 'em', AN_HIGHLIGHT_CLASS );
	portableNormalize( this.contentElement );
	removeClass( this.element, AN_ANNOTATED_CLASS );
	return annotations;
}

/*
 * Remove an individual annotation from a post
 */
PostMicro.prototype.removeAnnotation = function ( annotation )
{
	var next = this.removeNote( annotation );
	this.removeHighlight( annotation );
	return null == next ? null : next.annotation;
}

/*
 * Remove an note from the displayed list
 * Returns the next list item in the list
 */
PostMicro.prototype.removeNote = function( annotation )
{
	var listItem = document.getElementById( AN_ID_PREFIX + annotation.id );
	var next = listItem.nextSibling;
	listItem.parentNode.removeChild( listItem );
	listItem.annotation = null; // dummy item won't have this field
	clearEventHandlers( listItem, true );	
	return next;
}

/*
 * Recursively remove highlight markup
 */
PostMicro.prototype.removeHighlight = function ( annotation )
{
	var contentElement = this.contentElement;
	var highlights = getChildrenByTagClass( contentElement, 'em', AN_ID_PREFIX + annotation.id, null, null );
	for ( var i = 0;  i < highlights.length;  ++i )
		highlights[ i ].annotation = null;
	stripMarkup( contentElement, 'em', AN_ID_PREFIX + annotation.id );
	portableNormalize( contentElement );
}


/* ************************ Display Actions ************************ */
/* These are called by event handlers.  Unlike the handlers, they are
 * not specific to controls or events (they should make no assumptions
 * about the event that triggered them). */

/*
 * Indicate an annotation is under the mouse cursor by lighting up the note and the highlight
 * If flag is false, this will remove the lit-up indication instead.
 */
PostMicro.prototype.hoverAnnotation = function( annotation, flag )
{
	// Activate the note
	var noteNode = document.getElementById( AN_ID_PREFIX + annotation.id );
	if ( flag )
		addClass( noteNode, AN_HOVER_CLASS );
	else
		removeClass( noteNode, AN_HOVER_CLASS );

	// Activate the highlighted areas
	var highlights = getChildrenByTagClass( this.contentElement, null, AN_HIGHLIGHT_CLASS, null, null );
	for ( var i = 0;  i < highlights.length;  ++i )
	{
		var node = highlights[ i ];
		// Need to change to upper case in case this is HTML rather than XHTML
		if ( node.tagName.toUpperCase( ) == 'EM' && node.annotation == annotation )
		{
			if ( flag )
				addClass( node, AN_HOVER_CLASS );
			else
				removeClass( node, AN_HOVER_CLASS );
		}
	}
}

/*
 * Called to start editing a new annotation
 * the annotation isn't saved to the db until edit completes
 */
PostMicro.prototype.createAnnotation = function( annotation )
{
	// Ensure the window doesn't scroll by saving and restoring scroll position
	var scrollY = getWindowYScroll( );
	var scrollX = getWindowXScroll( );

	annotation.isLocal = true;
	annotation.isEditing = true;
	// Show the annotation and highlight
	this.addAnnotation( annotation );
	// Focus on the text edit
	var noteElement = document.getElementById( AN_ID_PREFIX + annotation.id );
	var editElement = getChildByTagClass( noteElement, 'textarea', null, null );
	// Sequencing here (with focus last) is important
	this.repositionNotes( noteElement.nextSibling );
	editElement.focus( );
	// Just in case - IE can't get it right when editing, so I don't trust it
	// on create either, even if it does work for me.
	if ( 'exploder' == detectBrowser( ) )
		editElement.focus( );
	
	window.scrollTo( scrollX, scrollY );
}

/*
 * Save an annotation after editing
 */
PostMicro.prototype.saveAnnotation = function( annotation )
{
	// Ensure the window doesn't scroll by saving and restoring scroll position
	var scrollY = getWindowYScroll( );
	var scrollX = getWindowXScroll( );
	
	var listItem = document.getElementById( AN_ID_PREFIX + annotation.id );
	var editNode = getChildByTagClass( listItem, 'textarea', null, null );
	
	// Check the length of the note.  If it's too long, do nothing, but restore focus to the note
	// (which is awkward, but we can't save a note that's too long, we can't allow the note
	// to appear saved, and truncating it automatically strikes me as an even worse solution.) 
	if ( editNode.value.length > MAX_NOTE_LENGTH )
	{
		alert( getLocalized( 'note too long' ) );
		editNode.focus( );
		return false;
	}
	
	// don't allow this to happen more than once
	if ( ! annotation.isEditing )
		return false;
	this.hoverAnnotation( annotation, false );
	annotation.isEditing = false;
	annotation.note = editNode.value;

	// Replace the editable note display
	this.removeNote( annotation );
	var noteElement = this.showNote( this.getAnnotationIndex( annotation ), annotation );
	
    // rgrp: comment this out as it breaks ...
	// this.repositionNotes( noteElement.nextSibling );
	
	// The annotation is local and needs to be created in the DB
	if ( annotation.isLocal )
	{
		var postMicro = this;
		var f = function( url ) {
			// update the annotation with the created ID
			var id = url.substring( url.lastIndexOf( '/' ) + 1 );
			annotation.id = id;
			annotation.isLocal = false;
			var noteElement = document.getElementById( AN_ID_PREFIX + '0' );
			noteElement.id = AN_ID_PREFIX + annotation.id;
			var highlightElements = getChildrenByTagClass( postMicro.contentElement, 'em', AN_ID_PREFIX + '0', null, null );
			for ( var i = 0;  i < highlightElements.length;  ++i )
			{
				removeClass( highlightElements[ i ], AN_ID_PREFIX + '0' );
				addClass( highlightElements[ i ], AN_ID_PREFIX + annotation.id );
			}
		};
		annotation.url = this.url;
		
		// IE may have made a relative URL absolute, which could cause problems
		if ( null != window.annotationUrlBase
			&& annotation.url.substring( 0, window.annotationUrlBase.length ) == window.annotationUrlBase )
		{
			annotation.url = annotation.url.substring( window.annotationUrlBase.length );
		}

		annotation.note = editNode.value;
		annotation.title = this.title;
		annotation.author = this.author;
		window.annotationService.createAnnotation( annotation, f );
	}
	// The annotation already exists and needs to be updated
	else
	{
		annotation.note = editNode.value;
		window.annotationService.updateAnnotation( annotation, null );
	}
	
	window.scrollTo( scrollX, scrollY );
	return true;
}

/*
 * Delete an annotation
 */
PostMicro.prototype.deleteAnnotation = function( annotation )
{
	// Ensure the window doesn't scroll by saving and restoring scroll position
	var scrollY = getWindowYScroll( );
	var scrollX = getWindowXScroll( );

	// Delete it on the server
	window.annotationService.deleteAnnotation( annotation.id, null );
	
	// Find the annotation
	var next = this.removeAnnotation( annotation );
	if ( null != next )
	{
		var nextElement = document.getElementById( AN_ID_PREFIX + next.id );
		this.repositionNotes( nextElement );
	}
	annotation.destruct( );
	
	window.scrollTo( scrollX, scrollY );
}


/* ************************ Event Handlers ************************ */
/* Each of these should capture an event, obtain the necessary information
 * to execute it, and dispatch it to something else to do the work */

/*
 * Mouse hovers over an annotation note or highlight
 */
function _hoverAnnotation( event )
{
	var post = getNestedFieldValue( this, 'post' );
	var annotation = getNestedFieldValue( this, 'annotation' );
	post.hoverAnnotation( annotation, true );
}

/*
 * Mouse hovers off an annotation note or highlight
 */
function _unhoverAnnotation( event )
{
	// IE doesn't have a source node for the event, so use this
	var post = getNestedFieldValue( this, 'post' );
	var annotation = getNestedFieldValue( this, 'annotation' );
	post.hoverAnnotation( annotation, false );
}

/*
 * Click on annotation to edit it
 */
function _editAnnotation( event )
{
	event = getEvent( event );
	stopPropagation( event );
	var post = getNestedFieldValue( this, 'post' );
	var annotation = getNestedFieldValue( this, 'annotation' );
	if ( ! annotation.isDeleted )
	{
		// Ensure the window doesn't scroll by saving and restoring scroll position
		var scrollY = getWindowYScroll( );
		var scrollX = getWindowXScroll( );
		
		annotation.isEditing = true;
		var next = post.removeNote( annotation );
		var noteElement = post.showNote( post.getAnnotationIndex( annotation ), annotation );
		post.repositionNotes( noteElement.nextSibling );
		var editElement = getChildByTagClass( noteElement, 'textarea', null, null );
		// It is absolutely essential that the element get the focus - otherwise, the
		// textarea will sit around looking odd until the user clicks *in* and then *out*,
		// which behavior would be most unimpressive.
		editElement.focus( );
		// Yeah, ain't IE great.  You gotta focus TWICE for it to work.  I don't
		// want to burden other browsers with its childish antics.
		if ( 'exploder' == detectBrowser( ) )
			editElement.focus( );
		
		window.scrollTo( scrollX, scrollY );
	}
}

/*
 * Hit a key while editing an annotation
 */
function _editKeyDown( event )
{
	event = getEvent( event );
	var target = getEventTarget( event );
	var post = getNestedFieldValue( target, 'post' );
	var annotation = getNestedFieldValue( target, 'annotation' );
	if ( event.keyCode == 13 )
	{
		post.saveAnnotation( annotation );
		return false;
	}
	// should check for 27 ESC to cancel edit
	else
		return true;
}

/*
 * Annotation edit loses focus
 */
function _saveAnnotation( event )
{
	event = getEvent( event );
	stopPropagation( event );
	var post = getNestedFieldValue( this, 'post' );
	var annotation = getNestedFieldValue( this, 'annotation' );
	post.saveAnnotation( annotation );
}

/*
 * Click annotation delete button
 */
function _deleteAnnotation( event )
{
	event = getEvent( event );
	stopPropagation( event );
	var post = getNestedFieldValue( this, 'post' );
	var annotation = getNestedFieldValue( this, 'annotation' );
	post.deleteAnnotation( annotation );
}

/*
 * Click annotation access button
 */
function _toggleAnnotationAccess( event )
{
	event = getEvent( event );
	stopPropagation( event );

	var annotation = getNestedFieldValue( this, 'annotation' );
	var accessButton = event.target;

	annotation.access = annotation.access == 'public' ? 'private' : 'public';
	window.annotationService.updateAnnotation( annotation, null );
	accessButton.removeChild( accessButton.firstChild );
	accessButton.appendChild( document.createTextNode( annotation.access == 'public' ? AN_SUN_SYMBOL : AN_MOON_SYMBOL ) );
	accessButton.setAttribute( 'title', annotation.access == 'public' ?
		getLocalized( 'public annotation' ) : getLocalized( 'private annotation' ) );
}

/*
 * Hit any key in document
 */
function _keyupCreateAnnotation( event )
{
	event = getEvent( event );
	if ( event.keyCode == 13 )
	{
		if ( createAnnotation( null, false ) )
			stopPropagation( event );
	}
}

/*
 * Alerts the user, then refetches all annotations from the server
 * Called by XMLHTTP callbacks if an operation fails
 *
 * Not yet implemented - need to get the URL from somewhere
function _refreshFromServer( s )
{
	alert( s );
	showAllAnnotations( );
}
 */

/* ************************ User Functions ************************ */

/*
 * Show all annotations on the page
 * There used to be showAnnotations and hideAnnotations functions which could
 * apply to individual posts on a page.  Unused, I removed them - they added
 * complexity because annotations needed to be stored but not displayed.  IMHO,
 * the best way to do this is with simple dynamic CSS (using display:none).
 */
function showAllAnnotations( url )
{
	window.annotationService.listAnnotations( url, _showAllAnnotationsCallback );
	var bodyElement = document.getElementsByTagName( 'body' )[ 0 ];
	// Charming.  IE is as thick as a brick.
	addClass( bodyElement, AN_ANNOTATED_CLASS );
	if ( window.annotationService.username == window.annotationThisUser )
		addClass( bodyElement, AN_SELFANNOTATED_CLASS );
}

function _showAllAnnotationsCallback( xmldoc )
{
	var annotations = parseAnnotationXml( xmldoc );
	var postElements = getChildrenByTagClass( document.documentElement, null, PM_POST_CLASS, null, _skipPostContent );
	for ( var i = 0;  i < postElements.length;  ++i )
	{
		// Hide any range mismatch error
		removeClass( postElements[ i ], AN_RANGEMISMATCH_ERROR_CLASS );
		// should also destruct each annotation
		var destructAnnotations = getPostMicro( postElements[ i ] ).removeAnnotations( );
		for ( var j = 0;  j < destructAnnotations.length;  ++j )
			destructAnnotations[ j ].destruct( );
		portableNormalize( postElements[ i ] );
		postElements[ i ] = null;	// prevent IE leaks
	}
	// This is the number of annotations that could not be displayed because they don't
	// match the content of the document.
	var annotationErrorCount = 0;
	for ( i = 0;  i < annotations.length;  ++i )
	{
		var post = annotations[ i ].post;
		if ( -1 == post.addAnnotation( annotations[ i ] ) )
		{
			++annotationErrorCount;
			// Make the error message visible by adding a class which can match a CSS
			// rule to display the error appropriately.
			// This doesn't work on... wait for it... Internet Explorer.  However, I don't
			// want to directly display a specific element or add content, because that
			// would be application-specific.  For now, IE will have to do without.
			addClass( post.element, AN_RANGEMISMATCH_ERROR_CLASS );
			// This was the alternative Moodle-specific solution:
			//var errorElement = getChildByTagClass( post.element, null, 'range-mismatch', _skipPostContent );
			//if ( null != errorElement )
			//	errorElement.style.display = 'block';
		}
	}
	annotations = null;
}

/*
 * Hide all annotations on the page
 */
function hideAllAnnotations( url )
{
	var postElements = getChildrenByTagClass( document.documentElement, null, PM_POST_CLASS, null, _skipPostContent );
	for ( var i = 0;  i < postElements.length;  ++i )
	{
		removeClass( postElements[ i ], AN_RANGEMISMATCH_ERROR_CLASS );
		if ( postElements[ i ].post )
		{
			var annotations = postElements[ i ].post.removeAnnotations( );
			for ( var j = 0;  j < annotations.length;  ++j )
				annotations[ j ].destruct( );
			postElements[ i ] = null;	// prevent IE leaks
		}
	}
	var bodyElement = document.getElementsByTagName( 'body' )[ 0 ];
	removeClass( bodyElement, AN_ANNOTATED_CLASS );
	removeClass( bodyElement, AN_SELFANNOTATED_CLASS );
}

function _skipSmartCopy( node )
{
	return hasClass( node, 'smart-copy' );
}

/*
 * Create a highlight range based on user selection
 * This is not in the event handler section above because it's up to the calling
 * application to decide what control creates an annotation.  Deletes and edits,
 * on the other hand, are built-in to the note display.
 */
function createAnnotation( postId, warn )
{
	// Test for selection support (W3C or IE)
	if ( ( ! window.getSelection || null == window.getSelection().rangeCount )
		&& null == document.selection )
	{
		if ( warn )
			alert( getLocalized( 'browser support of W3C range required for annotation creation' ) );
		return false;
	}
		
	var range = getPortableSelectionRange();
	if ( null == range )
	{
		if ( warn )
			alert( getLocalized( 'select text to annotate' ) );
		return false;
	}
	
	// Check for an annotation with id 0.  If one exists, we can't send another request
	// because the code would get confused by the two ID values coming back.  In that
	// case (hopefully very rare), silently fail.  (I figure the user doesn't want to
	// see an alert pop up, and the natural human instinct would be to try again).
	if ( null != document.getElementById( AN_ID_PREFIX + '0' ) )
		return;
	
	if ( null == postId )
	{
		var contentElement = getParentByTagClass( range.startContainer, null, PM_CONTENT_CLASS, false, null );
		if ( null == contentElement )
			return false;
		postId = getParentByTagClass( contentElement, null, PM_POST_CLASS, true, _skipPostContent ).id;
	}
	var post = document.getElementById( postId ).post;
	var annotation = annotationFromTextRange( post, range );
	annotation.userid = window.annotationService.username;
	if ( null == annotation )
	{
		if ( warn )
			alert( getLocalized( 'invalid selection' ) );
		return false;
	}
	
	// Check to see whether the quote is too long (don't do this based on the raw text 
	// range because the quote strips leading and trailing spaces)
	if ( annotation.quote.length > MAX_QUOTE_LENGTH )
	{
		annotation.destruct( );
		if ( warn )
			alert( getLocalized( 'quote too long' ) );
		return false;
	}
	
	post.createAnnotation( annotation );
	return true;
}


/* ************************ Annotation Class ************************ */
/*
 * This is a data-only class with (almost) no methods.  This is because all annotation
 * function either affect the display or hit the server, so more properly belong
 * to AnnotationService or PostMicro.
 * An annotation is based on a selection range relative to a contentElement.
 * The ID of a new range is 0, as it doesn't yet exist on the server.
 */
function Annotation( post, range )
{
	if ( null != post )
	{
		this.container = post.contentElement;
		this.quote_author = post.author;
		this.quote_title = post.title;
	}
	this.range = range;
	this.post = post;
	this.id = 0;
	this.note = '';
	this.access = 'public';
	this.quote = '';
	this.isLocal = false;
	this.isEditing = false;
	return this;
}

function compareAnnotationRanges( a1, a2 )
{
	return compareWordRanges( a1.range, a2.range );
}

function annotationFromTextRange( post, textRange )
{
	var range = textRangeToWordRange( textRange, post.contentElement, _skipSmartcopy );
	if ( null == range )
		return null;  // The range is probably invalid (e.g. whitespace only)
	var annotation = new Annotation( post, range );
	// Can't just call toString() to grab the quote from the text range, because that would
	// include any smart copy text.
	annotation.quote = getTextRangeContent( textRange, _skipSmartcopy );
	//annotation.quote = textRange.toString( );
	return annotation;
}

/*
 * Destructor to prevent IE memory leaks
 */
Annotation.prototype.destruct = function( )
{
	this.container = null;
	this.post = null;
	if ( this.range && this.range.destroy )
		this.range.destroy( );
	this.range = null;
}
