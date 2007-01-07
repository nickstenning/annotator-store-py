/*
 * range.js
 *
 * Requires domutil.js 
 *
 * Support for different kinds of text range (including the W3C Range object
 * and the TextRange object in IE)
 */

function getPortableSelectionRange( )
{
	var range;
	// W3C Range object (Mozilla)
	if ( window.getSelection )
	{
		var selection = window.getSelection( );
		if ( null == selection.rangeCount || 0 == selection.rangeCount )
			return null;
		return selection.getRangeAt( 0 );
	}
	// Internet Explorer
	else if ( document.selection )
	{
		return getSelectionRangeIE( );
		if ( null == range )
			return null;
	}
	// No support
	else
		return null;
}	

/*
 * Get the position and length of a text selection in Internet Explorer
 * returns:
 * .container
 * .offset
 * .length
 */
function getSelectionRangeIE()
{
	// Return if there's no selection
	if ( document.selection.type == 'None' )
		return null;
	
	// This will be the return value
	var result = new Object();
	
	// Now get the selection and its length.
	// I will try to restrain my frustration.  Because there's a mismatch between the text
	// that IE returns here, and the sequence of text nodes it displays in the DOM tree.
	// If there's a paragraph break, for example, IE will return CR-LF here.  But in the DOM,
	// it will not report any whitespace between the end of one and the start of the other.
	// So, *we can't trust this length*.  Instead, calculate a non-whitespace length and work
	// with *that*.  I will not swear.  I will not swear.  I will not strike microsoft in its
	// big bloody nose with a cluestick the size of manhattan.  Morons.
	var range = document.selection.createRange( );
	var length = range.text.length;
	var nws_length = range.text.replace( /(\s|\u00a0)/g, '' ).length;
	
	// It is necessary to shrink the range so that there are no element
	// boundaries within it.  Otherwise, IE will add missing start and
	// end tags on copy, and add more strange tags on paste, so writing
	// the marker wouldn't be safe.
	range.moveEnd( 'character', 1 - length );

	// Write a marker with a unique ID at the start of the range.
	// A search for this will find the location of the selection.
	var html = range.htmlText;
	range.pasteHTML( '<span id="rangeStart"></span>' + html );
	var markerElement = document.getElementById( 'rangeStart' );
	
	// Find the location of the marker relative to its parent element
	if ( markerElement.previousSibling )
	{
		result.startContainer = markerElement.previousSibling;
		result.startOffset = getContentOffset( result.startContainer, markerElement, 0, null );
	}
	else
	{
		// Special case, because startContainer *must* be a text node.  See below:
		// in this case, after the marker has been deleted the start container must
		// be updated.
		result.startContainer = markerElement.parentNode;
		result.startOffset = 0;
	}
	
	// If the text starts with a space, IE will strip it, so we need to add it back in.
	if ( html.substr( 0, 1 ) == ' ' )
		markerElement.parentNode.insertBefore( document.createTextNode( ' ' ), markerElement );
	// Remove the marker.
	markerElement.parentNode.removeChild( markerElement );
	portableNormalize( markerElement.parentNode );
	
	var walker;
	// Make sure the start marker is a text node.  This may not be the case if there was no node 
	// preceding the marker (see special case above).
	if ( TEXT_NODE != result.startContainer.nodeType )
	{
		walker = new DOMWalker( result.startContainer );
		while ( null != walker.node && TEXT_NODE != walker.node.nodeType )
			walker.walk( ! _skipSmartcopy( walker.node ) );
		result.startContainer = walker.node;
	}
	
	// Convert the length to a container,offset pair as used by W3C
	//var end = walkUntilLen( result.startContainer, result.startOffset + length );
	//result.endContainer = end.container;
	//result.endOffset = end.offset;
	
	// Now we have to count the correct number of non-whitespace characters (see explanation
	// of Microsoft mental disibility above).
	
	var remains = nws_length;
	walker = new DOMWalker( result.startContainer )
	while ( null != walker.node && remains > 0 )
	{
		if ( TEXT_NODE == walker.node.nodeType )
		{
			// So that we only need to compare with spaces later
			var nodeStr = walker.node.nodeValue.replace( /\s/g, ' ' );
			nodeStr = nodeStr.replace( /\u00a0/g, ' ' );
			// Iterate over characters, counting only those that aren't spaces
			var i = ( walker.node == result.startContainer ) ? result.startOffset : 0;
			while ( i < nodeStr.length )
			{
				if ( ' ' != nodeStr.charAt( i ) )
					--remains;
				// If we've counted enough spaces, then this is the end point
				if ( 0 == remains )
				{
					result.endContainer = walker.node;
					result.endOffset = i + 1;
					break;
				}
				++i;
			}
		}
		walker.walk( ! _skipSmartcopy( walker.node ) );
	}
	
	// A full implementation would need to replace the selection here, because
	// adding and removing text clears it.  For annotation, that's not necessary.
	
	return result;
}


/*
 * Create a normalized range, that is, a range consisting of a start and length, both
 * calculated from the same containing element, which is passed in.
 * skipClass - any elements with this class will not be included in the count
 */
function NormalizedRange( range, rel, fskip )
{
	// must ensure that the range starts and ends within the passed rel element
	if ( ! isElementDescendant( range.startContainer, rel ) || ! isElementDescendant( range.endContainer, rel ) )
		return null;

	var nrange = new Object();
	nrange.container = rel;
	nrange.offset = getContentOffset( rel, range.startContainer, range.startOffset, fskip );
	nrange.length = getContentOffset( rel, range.endContainer, range.endOffset, fskip ) - nrange.offset;
	return nrange;
}

/*
 * Get the text inside a TextRange
 * While the built-in toString() method would do this, we need to skip content
 * (such as smart copy text).  This is in fact designed to work with smartcopy, so there
 * are certain cases it may not handle.  This also assumes that the range points to
 * text nodes at the start and end (otherwise walking won't work).
 */
function getTextRangeContent( range, fskip )
{
	var s;
	// Special case
	if ( range.startContainer == range.endContainer )
		s = range.startContainer.nodeValue.substring( range.startOffset, range.endOffset );
	else
	{
		s = range.startContainer.nodeValue.substring( range.startOffset, range.startContainer.length );
		var walker = new DOMWalker( range.startContainer );
		walker.walk( );
		while ( null != walker.node && walker.node != range.endContainer )
		{
			if ( TEXT_NODE == walker.node.nodeType )
				s += walker.node.nodeValue;
			else if ( ELEMENT_NODE == walker.node.nodeType ) //&& 'inline' != htmlDisplayModel( walker.node.tagName ) )
				s += ' ';
			walker.walk( ! fskip( walker.node ) );	
		}
	
		// Pick up content from the last node
		s += range.endContainer.nodeValue.substring( 0, range.endOffset );
		walker.destroy( );
	}
	
	// Normalize spaces
	s = s.replace( /(\s|\u00a0)\s*/g, '$1' );
	s = s.replace( /(\s|\u00a0)$/, '' );
	s = s.replace( /^(\s|\u00a0)/, '' );
	
	return s;
}

/*
 * Get the length of a text range, in characters
 */
function getTextRangeLength( range, fskip )
{
	// We might be pointing to a skipable node to start with.  Move past it.
	var node = range.startContainer;
	if ( fskip( node ) )
		node = walkNextNode( node, fskip );

	var len = 0;
	while ( null != node )
	{
		// grab text if appropriate
		if ( TEXT_NODE == node.nodeType )
		{
			// This case might be broken;  I don't think I've ever tested it.
			if ( node == range.startContainer && node == range.endContainer )
				return range.endOffset - range.startOffset;
			else if ( node == range.startContainer )
				len = node.length - range.startOffset; 
			else if ( node == range.endContainer )
				return len + range.endOffset;
		}
		node = walkNextNode( node, fskip );
			
	}
	return -1;
}

/*
 * State values used by state machines
 */
STATE_SPACE = 0
STATE_WORD = 1
STATE_TARGET_SPACE = 2
STATE_TARGET_WORD = 3
STATE_FALL_FORWARD = 4
STATE_DONE = 5

/*
 * Convert a text range to a word range
 * This is rather inefficient, because it starts at the beginning of the range for both points.
 * The second point will always follow the first, so with a bit of work the state machine could
 * continue from that point.
 */
function textRangeToWordRange( textRange, rel, fskip )
{
	var range = new WordRange( );
	range.start = nodePointToWordPoint( textRange.startContainer, textRange.startOffset, rel, true, fskip );
	range.end = nodePointToWordPoint( textRange.endContainer, textRange.endOffset, rel, false, fskip );
	if ( null == range.start || null == range.end )
	{
		if ( range.start )
			range.start.destroy( );
		if ( range.end )
			range.end.destroy( );
		return null;
	}
	return range;
}

/*
 * Convert a word range to a text range
 * This is also inefficient, because annotation calls it repeatedly, each time from the start
 * of the document.  A better version would take advantage of the fact that highlights are
 * always shown in order.  Also, it suffers from the same inefficiency as textRangeToWordRange.
 */
function wordRangeToTextRange( wordRange, rel, fskip )
{
	trace( 'word-range', 'wordRangeToTextRange: ' + wordRange.toString( ) );
	var startPoint = wordPointToNodePoint( wordRange.start, rel, fskip );
	var endPoint = wordPointToNodePoint( wordRange.end, rel, fskip );
	var range = new TextRange( startPoint.container, startPoint.offset, endPoint.container, endPoint.offset );
	startPoint.destroy( );
	endPoint.destroy( );
	return range;
}

function TextRange( startContainer, startOffset, endContainer, endOffset )
{
	this.startContainer = startContainer;
	this.startOffset = startOffset;
	this.endContainer = endContainer;
	this.endOffset = endOffset;
	return this;
}

TextRange.prototype.destroy = function( )
{
	this.startContainer = null;
	this.endContainer = null;
}

/*
 * Convert a (container,offset) pair into a word count from containing node named rel
 * container must be the text node containing the point
 * The first representation is browser-specific, but a word count is not.
 * A word is defined as a continuous sequence of non-space characters.  Inline elements
 * are not considered word separators, but block-level elements are.
 * fallBack - if position ends following whitespace, count an extra word?
 */
function nodePointToWordPoint( container, offset, rel, fallForward, fskip )
{
	trace( 'word-range', 'nodePointToWordPoint( ' + container + ',' + offset + ',' + rel + ')' );
	var state = new NodeToWordPoint_Machine( container, offset, rel, fallForward );
	RecurseOnElement( state, rel, fskip );
	if ( STATE_DONE == state.state )
	{
		var point = state.getPoint( );
		state.destroy( );
		return point;
	}
	else
	{
		trace( null, 'Point not found.' );
		return null;
	}
}

NodeToWordPoint_Machine.prototype.trace = function( input )
{
	trace( 'word-range', 'State ' + this.state + ' at ' + this.words + '.' + this.chars + ' (' + this.offset + ' offset) input "' + input + '"' );
}

function RecurseOnElement( state, node, fskip )
{
	if ( ELEMENT_NODE == node.nodeType && ( null == fskip || ! fskip( node ) ) )
	{
		var r = state.startElement( node );
		if ( STATE_DONE == state.state )
			return true;
		if ( r )
		{
			for ( var child = node.firstChild;  null != child;  child = child.nextSibling )
			{
				RecurseOnElement( state, child, fskip )
				if ( STATE_DONE == state.state )
					return true;
			}
			state.endElement( node );
		}
		if ( STATE_DONE == state.state )
			return true;
	}
	else if ( TEXT_NODE == node.nodeType || CDATA_SECTION_NODE == node.nodeType )
	{
		state.text( node );
		if ( STATE_DONE == state.state )
			return true;
	}
	return false;
}


function NodeToWordPoint_Machine( container, offset, rel, fallForward )
{
	this.targetContainer = container;
	this.targetOffset = offset;
	this.fallForward = fallForward;
	this.container = rel;
	this.words = 0;
	this.chars = 0;
	this.state = STATE_SPACE;
	this.offset = 0;
	return this;
}

NodeToWordPoint_Machine.prototype.destroy = function( )
{
	this.targetContainer = null;
	this.container = null;
}

function WordPoint( )
{
	this.container = null;
	this.words = 0;
	this.chars = 0;
	return this;
}

WordPoint.prototype.destroy = function( )
{
	this.container = null;
}

/*
 * Compare two points to see which comes first.  The containers of the points are not part
 * of the comparison.
 */
function compareWordPoints( p1, p2 )
{
	// Don't compare containers;  otherwise the global annotation list returned by the server
	// needs to be broken down into sub-lists, which is expensive.
//	if ( p1.container != p2.container )
//		throw "Invalid WordPoint comparison - containers are " + p1.container + ' and ' + p2.container + ".";
	if ( p1.words < p2.words || p1.words == p2.words && p1.chars < p2.chars )
		return -1;
	else if ( p1.words > p2.words || p1.words == p2.words && p1.chars > p2.chars )
		return 1;
	else
		return 0;
}

WordPoint.prototype.toString = function( )
{
	//return "word('space'," + this.words + ') offset(' + this.chars + ')';
	return this.words + '.' + this.chars;
}

WordPoint.prototype.fromString = function( s, container )
{
	//var matches = s.match( /word\(['"]space['"],(\d+)\)\s*offset\((\d+)\)\s*$/ );
	//this.words = matches[ 0 ];
	//this.chars = matches[ 1 ];
	this.container = container;
	var parts = s.split( '.' );
	this.words = ( parts[ 0 ] ) * 1;
	this.chars = ( parts[ 1 ] ) * 1;
}

function WordRange()
{
	this.container = null;
	this.start = null;
	this.end = null;
	return this;
}

WordRange.prototype.destroy = function( )
{
	if ( null != this.start )
		this.start.destroy( );
	if ( null != this.end )
		this.end.destroy( );
}

function compareWordRanges( r1, r2 )
{
	var cstart = compareWordPoints( r1.start, r2.start );
	var cend = compareWordPoints( r1.end, r2.end );
	if ( cstart < 0 || cstart == 0 && cend < 0 )
		return -1;
	else if ( cstart > 0 || cstart == 0 && cend > 0 )
		return 1;
	else
		return 0;
}

WordRange.prototype.toString = function( )
{
	return this.start.toString( ) + ' ' + this.end.toString( );
}

WordRange.prototype.fromString = function( s, container )
{
	s = s.replace( /(\s|\u00a0)+/g, ' ' );
	var parts = s.split( ' ' );
	this.start = new WordPoint( );
	this.start.fromString( parts[ 0 ], container );
	this.end = new WordPoint( );
	this.end.fromString( parts[ 1 ], container );
}

NodeToWordPoint_Machine.prototype.getPoint = function( )
{
	var point = new WordPoint( );
	point.container = this.container;
	point.words = this.words;
	point.chars = this.chars;
	return point;
}
	
/* States:  space, word, fall-forward */

NodeToWordPoint_Machine.prototype.startElement = 
NodeToWordPoint_Machine.prototype.endElement = function( node )
{
	this.trace( '<' + node.tagName + '>' );
	if ( 'inline' != htmlDisplayModel( node.tagName ) )
	{
		if ( STATE_WORD == this.state )
			this.state = STATE_SPACE;
		else if ( STATE_FALL_FORWARD == this.state )
		{
			this.state = STATE_DONE;
			return;
		}
	}
	if ( node == this.targetContainer )
	{
		if ( STATE_WORD == this.state )
			this.state == STATE_TARGET_WORD;
		else if ( STATE_SPACE == this.state )
			this.state == STATE_TARGET_SPACE;
	}
	return true;
}

NodeToWordPoint_Machine.prototype.text = function( node )
{
	if ( node == this.targetContainer )
	{
		if ( 0 == this.targetOffset )
		{
			if ( this.fallForward )
			{
				if ( STATE_SPACE == this.state )
				{
					this.words += 1;
					this.chars = 0;
					this.state = STATE_DONE;
					return;
				}
				else
					this.state = STATE_FALL_FORWARD;
			}
			else
			{
				this.state = STATE_DONE;
				return;
			}
		}
		else
		{
			if ( STATE_SPACE == this.state )
				this.state = STATE_TARGET_SPACE;
			else if ( STATE_WORD == this.state )
				this.state = STATE_TARGET_WORD;
		}
		trace( 'word-range', 'In container, state ' + this.state + ' at ' + this.words + '.' + this.chars + ' looking for offset ' + this.targetOffset );
	}
	
	s = node.nodeValue.replace( /(\s|\u00a0)/g, ' ' );
	trace( 'word-range', "Searching in:\n" + s );
	for ( var i = 0;  i < s.length;  ++i )
	{
		var c = s.charAt( i );
		this.trace( c );
		if ( STATE_SPACE == this.state )
		{
			if ( ' ' != c )
			{
				this.chars = 1;
				this.words += 1;
				this.state = STATE_WORD;
			}
		}
		else if ( STATE_WORD == this.state )
		{
			if ( ' ' == c )
				this.state = STATE_SPACE;
			else
			{
				// Don't iterate through every character in the word.  This produces a noticeable
				// speed increase (gut instinct places it at 3-5x).  Also, don't optimize
				// STATE_TARGET_WORD - that's too much complexity for too little benefit. 
				var j = s.indexOf( ' ', i );
				if ( -1 == j )
					this.chars += 1;	// only action required for unoptimized version
				else
				{
					i = j;
					this.chars += j - i;
					this.state = STATE_SPACE;
				}
			}
		}
		else if ( STATE_TARGET_SPACE == this.state )
		{
			if ( ' ' != c )
			{
				this.chars = 1;
				this.words += 1;
				this.state = STATE_TARGET_WORD;
				trace( 'word-range', 'TARGET_SPACE -> TARGET_WORD, offset=' + (this.offset + 1) );
			}
			this.offset += 1;
			if ( this.offset == this.targetOffset )
			{
				if ( this.fallForward )
				{
					if ( this.state == STATE_TARGET_SPACE )
					{
						this.words += 1;
						this.chars = 0;
					}
					else
						this.state = STATE_FALL_FORWARD;
				}
				else
				{
					this.state = STATE_DONE;
					return;
				}
			}
		}
		else if ( STATE_TARGET_WORD == this.state )
		{
			this.offset += 1;
			if ( ' ' == c )
				this.state = STATE_TARGET_SPACE;
			else
				this.chars += 1;
			if ( this.offset == this.targetOffset )
			{
				if ( this.fallForward )
				{
					if ( ' ' == c )
					{
						this.words += 1;
						this.chars = 0;
						this.state = STATE_DONE;
						return;
					}
					else
						this.state = STATE_FALL_FORWARD;
				}
				else
				{
					trace( 'word-range', 'Success at ' + this.words + '.' + this.chars );
					this.state = STATE_DONE;
					return;
				}
			}
		}
		else if ( STATE_FALL_FORWARD == this.state )
		{
			if ( ' ' == c )
			{
				this.words += 1;
				this.chars = 0;
			}
			trace( 'word-range', 'Success: fall forward to ' + this.words + '.' + this.chars );
			this.state = STATE_DONE;
			return;
		}
	}

	// It is possible that this is the target container, but that there's no match yet
	// because we're trying to fall forward.
	// If this is the element and there's no match yet, perhaps fall forward
	if ( node == this.targetContainer && this.fallForward && this.offset == this.targetOffset )
		this.state = STATE_FALL_FORWARD;
	return;
}

function wordPointToNodePoint( point, rel, fskip )
{
	var state = new WordPointToNodePoint_Machine( point );
	RecurseOnElement( state, rel, fskip );
	if ( STATE_DONE == state.state )
		return state;
	else
		return null;
}

function WordPointToNodePoint_Machine( point )
{
	this.targetWords = point.words;
	this.targetChars = point.chars;
	this.state = STATE_SPACE;
	this.words = 0;
	this.container = null;
	this.offset = 0;
	this.chars = 0;
	return this
}

WordPointToNodePoint_Machine.prototype.destroy = function( )
{
	this.container = null;
}

WordPointToNodePoint_Machine.prototype.startElement = function( node )
{
	if ( STATE_WORD == this.state && 'inline' != htmlDisplayModel( node.tagName ) )
		this.state = STATE_SPACE;
	
	// See if the number of words is already stored in the node.  If so,
	// can we use the count and not bother counting within the node?
	if( null != node.rangeWordCount && node.rangeWordCount > 0 )
	{
		if ( this.words + node.rangeWordCount >= this.targetWords )
			return true;
		else
		{
			this.words += node.rangeWordCount;
			this.state = node.rangeEndState;
			this.chars = node.rangeEndChars;
			return false;
		}
	}
	else 
	{
		this.startWordCount = this.words;
		return true;
	}
}

WordPointToNodePoint_Machine.prototype.endElement = function( node )
{
	// Store the number of words and the end state in the node
	// (these figures are the same no matter whether the node is part of multiple
	// enclosing range base nodes)
	if ( STATE_WORD == this.state && 'inline' != htmlDisplayModel( node.tagName ) )
		this.state = STATE_SPACE;
	if ( this.startWordCount )
	{
		node.rangeEndState = this.state;
		node.rangeWordCount = this.words - this.startWordCount;
		node.rangeEndChars = this.chars;
		delete this.startWordCount;
	}
}

WordPointToNodePoint_Machine.prototype.trace = function( input )
{
	trace( 'word-range', 'State ' + this.state + ' at ' + this.words + '.' + this.chars + ' input "' + input + '"' );
}

WordPointToNodePoint_Machine.prototype.text = function( node )
{
	var s = node.nodeValue.replace( /(\s|\u00a0)/g, ' ' );
	for ( var i = 0;  i < s.length;  ++i )
	{
		var c = s.charAt( i );
		//this.trace( c + '(' + i + ')' );
		if ( STATE_SPACE == this.state )
		{
			if ( ' ' != c )
			{
				this.state = STATE_WORD;
				this.words += 1;
				this.chars = 1;
				if ( this.words == this.targetWords )
				{
					this.state = STATE_TARGET_WORD;
					if ( 0 == this.targetChars || 1 == this.targetChars)
					{
						// This is somewhat confusing, because it would appear that if the offset
						// should be zero, then perhaps it should actually be a non-zero offset
						// from a previous node.  But this algorithm looks for the tightest
						// bounds achievable with no leading or trailing spaces, so odd as it looks
						// this ternary operator test is correct.
						this.container = node;
						this.offset = ( 0 == this.targetChars ) ? i : i + 1;
						this.state = STATE_DONE;
						return;
					}
				}
			}
		}
		else if ( STATE_WORD == this.state )
		{
			if ( ' ' == c )
				this.state = STATE_SPACE;
			else
			{
				// Don't iterate through every character in the word.  This produces a noticeable
				// speed increase (gut instinct places it at 3-5x).  Also, don't optimize
				// STATE_TARGET_WORD - that's too much complexity for too little benefit. 
				var j = s.indexOf( ' ', i );
				if ( -1 == j )
					++this.chars;	// this is the only action required for unoptimized version
				else
				{
					i = j;
					this.chars += j - i;
					this.state = STATE_SPACE;
				}
			}
		}
		else if ( STATE_TARGET_WORD == this.state )
		{
			if ( ' ' == c )
			{
/*				if ( this.chars == this.targetChars )
				{
					this.container = node;
					this.offset = i;
					return true;
				}
				else
*/
				//trace( 'word-range', 'space - fail' );
				return false;  //fail
			}
			else
			{
				++this.chars;
				if ( this.chars == this.targetChars )
				{
					this.container = node;
					this.offset = i + 1;
					//trace( 'word-range', 'Found, offset=' + this.offset );
					this.state = STATE_DONE;
					return;
				}
			}
		}
	}
}


/*
 * Convert the start or end point of a TextRange to a simple XPointer representation
 * Actually, this isn't quite a real XPointer.
 * An XPointer would be id/1/5/2, but this returns
 * something more like 1/5/2:1+57, where 1 is a text node index and +57 is a character offset
 * Sue me.  I haven't figured out how XPointer specifies points for arbitrary
 * offsets;  I'm beginning to think it doesn't.  Also, note the missing ID:  this
 * is because the caller passes in the base node from which this is a reference.
 *
 * fskip - function, returns true if this element should not be included in the count
 * fflatten - function, returns true if this element's children should be considered to
 *   be of the parent element (for ignoring <em> annotation tags) 
 */
function nodeOffsetToPoint( container, offset, rel, fskip, fflatten )
{
	var pointer = 'point()[' + offset + ']';
	var node, element, x, tag;
	// Which text node?
	if ( TEXT_NODE == container.nodeType )
	{
		var x = 1;
		for ( node = container.previousSibling;  null != node;  node = node.previousSibling )
		{
			if ( TEXT_NODE == node.nodeType )
				x += 1;
		}
		pointer = 'text()[' + x + ']/' + pointer;
		element = container.parentNode;
	}
	else // This can only handle text and element nodes (no CDATA)
		element = container;
	while ( null != element && rel != element && DOCUMENT_NODE != element.nodeType )
	{
		x = 1;
		trace( 'xpointer', element );
		trace( 'xpointer', 'rel: ' + rel );
		tag = element.tagName.toLowerCase( );
		for ( node = element.previousSibling;  null != node;  node = node.previousSibling )
		{
			// Case insensitive on tag names;  ignores namespaces!
			if ( ELEMENT_NODE == node.nodeType && node.tagName.toLowerCase() == tag )
			{
				if ( null == fskip || ! fskip( node ) )
					// FLATTEN! #geof#
					++x;
			}
		}
		pointer = tag + '[' + x + ']/' + pointer;
		element = element.parentNode;
	}
	return 'xpointer(' + pointer + ')';
}


/*
 * Used for converting a (container,offset) pair as used by the W3C Range object
 * to a character offset relative to a specific element.
 */
function getContentOffset( rel, container, offset, fskip )
{
	var sofar = 0;
	
	// Start with rel and walk forward until we hit the range reference
	var node = rel;
	while ( node != container && node != null)
	{
		if ( TEXT_NODE == node.nodeType || CDATA_SECTION_NODE == node.nodeType )
			sofar += node.length;
		node = walkNextNode( node, fskip );
	}
	if ( null == node )
		return 0;

	// First case:  a character offset in a text node (most common case for selection ranges)
	if ( TEXT_NODE == node.nodeType || CDATA_SECTION_NODE == node.nodeType )
	{
		//trace( 'getContentOffset ' + container + ',' + offset + ' -> ' + (sofar+offset) );
		return sofar + offset;
	}
	// Second case:  a child element offset within a non-text node
	else
	{
		// Walk forward through child nodes until we hit the specified offset
		node = node.firstChild;
		for ( var i = 0;  i < offset;  ++i )
		{
			if ( null == node )
				debug( 'Error in getContentOffset:  invalid element offset' );
			sofar += nodeTextLength( node );
			node = node.nextSibling;
		}
		return sofar;
	}
}

