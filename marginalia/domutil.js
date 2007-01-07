/*
 * domutil.js
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
 *
 */

 // DOM constants
ELEMENT_NODE = 1;
TEXT_NODE = 3;
CDATA_SECTION_NODE = 4;
DOCUMENT_NODE = 9;

/*
 * Return the display model (inline, block, none, or unknown) for an HTML element
 */
function htmlDisplayModel( tagName )
{
	var model = HTML_CONTENT_MODEL[ tagName.toLowerCase() ];
	if ( null != model ) {
		return model[ 'model' ];
	}
}

/*
 * Is an HTML element valid within a specified element?
 * The table used here is generated from the HTML DTD by a Perl script.
 * Not all entities are not fully expanded (although the entity definitions are)
 * This keeps the size of that definition file down, which makes it smaller to download.
 */
function isValidHtmlContent( parentName, childName )
{
	childName = childName.toLowerCase( );
	var definitions = HTML_CONTENT_MODEL;
	var model = definitions[ parentName.toLowerCase() ];
	if ( null == model )
		return false;
	var content = model.content;
	if ( content[ childName ] )
		return true;
	else
	{
		for ( var child in content )
		{
			if ( child.charAt( 0 ) == '%' && definitions[ child ].content[ childName ] )
				return true;
		}
	}
	return false;
}


/*
 * Get an event
 */
function getEvent( event )
{
	if ( event )
		return event;		// usually W3C
	else
		return window.event;// usually IE
}

/* 
 * Get an event target
 * Because IE sucks
 */
function getEventTarget( event )
{
	return event.target ? event.target : event.srcElement;
}

/*
 * Fetch the local name for a node (i.e., without any namespace qualifier)
 */
function getLocalName( element )
{
	if ( element.localName )
		return element.localName;	// W3C implementation
	else
		return element.baseName;	// IE implementation
}

/*
 * Stop an event from bubbling
 */
function stopPropagation( event )
{
	if ( event.stopPropagation )
		event.stopPropagation();		// W3C
	else
		event.cancelBubble = true;	// IE
}

/*
 * Browser independent function to create an XMLHttpRequest ojbect
 */
function createAjaxRequest( )
{
	if ( window.XMLHttpRequest )
		return new XMLHttpRequest( );  // Gecko / XHTML / WebKit
	else
		return new ActiveXObject( "Microsoft.XMLHTTP" );  // MS IE
}

/*
 * Test whether a node has a certain class value
 */
function hasClass( element, className )
{
	if ( null == className )
		return false;
	var classNames = element.className.split( ' ' );
	for ( var i = 0;  i < classNames.length;  ++i )
	{
		if ( classNames[ i ] == className )
			return true;
	}
	return false;
}

/*
 * Fetch the first child with a given class attribute value
 */
function getChildByTagClass( node, tagName, className, fskip )
{
	if ( node == null )
		alert( "node not found tag=" + tagName + ", class=" + className );
	if ( node.nodeType == ELEMENT_NODE && ( ! fskip || ! fskip( node ) ) )
	{
		if ( null == tagName || tagName.toUpperCase( ) == node.tagName.toUpperCase( ) )
		{
			if ( null == className )
				return node;
			var classNames = node.className.split( ' ' );
			for ( var i = 0;  i < classNames.length;  ++i )
			{
				if ( classNames[ i ] == className )
					return node;
			}
		}
		if ( null != node.childNodes )
		{
			for ( var i = 0;  i < node.childNodes.length;  ++i )
			{
				var child = getChildByTagClass( node.childNodes[ i ], tagName, className );
				if ( child != null )
					return child;
			}
		}
	}
	return null;
}

/*
 * Get a child anchor (<a>) element by rel value
 */
function getChildAnchor( node, relName, fskip )
{
	if ( node == null )
		alert( "node not found tag=" + tagName + " (looking for rel=" + relName + ")");
	if ( node.nodeType == ELEMENT_NODE && ( ! fskip || ! fskip( node ) ) )
	{
		if ( 'A' == node.tagName.toUpperCase() || 'LINK' == node.tagName.toUpperCase() )
		{
			var rel = node.getAttribute( 'rel' );
			if ( null != rel )
			{
				var relNames = rel.split( ' ' );
				for ( var i = 0;  i < relNames.length;  ++i )
				{
					if ( relNames[ i ] == relName )
						return node;
				}
			}
			trace( null, 'rel=' + node.rel +' , href=' + node.getAttribute( 'rel' ) );
		}
		if ( null != node.childNodes )
		{
			for ( var i = 0;  i < node.childNodes.length;  ++i )
			{
				var child = getChildAnchor( node.childNodes[ i ], relName, fskip );
				if ( child != null )
					return child;
			}
		}
	}
	return null;
}

function getChildrenByTagClass( node, tagName, className, matches, fskip )
{
	if ( null == matches )
		matches = new Array( );
	if ( node == null )
		alert( "node not found tag=" + tagName + ", class=" + className );
	if ( node.nodeType == ELEMENT_NODE && ( ! fskip || ! fskip( node ) ) )
	{
		if ( null == tagName || tagName.toUpperCase( ) == node.tagName.toUpperCase( ) )
		{
			if ( null == className )
				matches[ matches.length ] = node;
			else if ( null != node.className )
			{
				var classNames = node.className.split( ' ' );
				for ( var i = 0;  i < classNames.length;  ++i )
				{
					if ( classNames[ i ] == className )
						matches[ matches.length ] = node;
				}
			}
		}
		for ( var i = 0;  i < node.childNodes.length;  ++i )
			getChildrenByTagClass( node.childNodes[ i ], tagName, className, matches );
	}
	return matches;
}

/*
 * Get the value of a named field in the first ancestor with that field
 */
function getNestedFieldValue( node, field )
{
	while ( null != node && ! node[ field ] )
		node = node.parentNode;
	return null == node ? null : node[ field ];
}

/*
 * Fetch the first parent with a given class attribute value
 * this should be fixed because there can be multiple class names listed in the class attribute
 * The fskip value works a little differently here.  This function guarantees that the result
 * node is not within an element for which fskip is true.
 */
function getParentByTagClass( theNode, tagName, className, topDown, fskip )
{
	var topResult = null;
	var bottomResult = null;
	for ( var node = theNode;  node != null && DOCUMENT_NODE != node.nodeType;  node = node.parentNode )
	{
		if ( fskip && fskip( node ) )
			topResult = bottomResult = null;
		else if ( ELEMENT_NODE == node.nodeType && ( null == tagName || tagName.toUpperCase( ) == node.tagName.toUpperCase( ) ) )
		{
			if ( null == className )
			{
				topResult = node;
				if ( null == bottomResult )
					bottomResult = node;
			}
			else
			{
				var classNames = node.className.split( ' ' );
				for ( var i = 0;  i < classNames.length;  ++i )
				{
					if ( classNames[ i ] == className )
					{
						topResult = node;
						if ( null == bottomResult )
							bottomResult = node;
					}
				}
			}
		}
	}
	return topDown ? topResult : bottomResult;
}
 
/*
 * Check whether a node is a descendant of another node
 */
function isElementDescendant( element, container )
{
	var parent = element;
	while ( parent != container && null != parent )
		parent = parent.parentNode;
	return parent == null ? false : true;
}

/*
 * Calculate the number of characters of text in a node
 * Does this work correctly with variable-length unicode characters?
 * Any elements with a class of skipClass are ignored
 */
function nodeTextLength( node, skipClass )
{
	// Base case
	if ( TEXT_NODE == node.nodeType || CDATA_SECTION_NODE == node.nodeType )
		return node.length;
	// Recurse
	else if ( ELEMENT_NODE == node.nodeType && ( null == skipClass || ! hasClass( node, skipClass ) ) )
	{
		var n = 0;
		for ( var i = 0;  i < node.childNodes.length;  ++i )
			n += nodeTextLength( node.childNodes[ i ] );
		return n;
	}
	else
		return 0;
}

/*
 * Uh-oh, there's a problem here:  block-level elements separate words, but
 * inline ones may not (e.g. there may be italics in the middle of a word).
 * Hmmm.
 */
function nodeWordCount( node, fskip )
{
	// Base case
	if ( TEXT_NODE == node.nodeType || CDATA_SECTION_NODE == node.nodeType )
	{
		// collapse and trim spaces
		var s = node.nodeValue.replace( /\s+/g, ' ' );
		s = s.replace( '^\s+', '' );
		s = s.replace( '\s+$', '' );
		
	}
	// Recurse
	else if ( ELEMENT_NODE == node.nodeType && ( null == fskip || ! fskip( node ) ) )
	{
		var n = 0;
		for ( var child = node.firstChild;  null != child;  child = child.nextSibling )
			n += nodeWordCount( child );
		return n;
	}
	else
		return 0;
}

/*
 * Return the text contained within a node, with all tags stripped (this is like casting to text in XPath)
 */
function getNodeText( node )
{
	if ( node.nodeType == TEXT_NODE || node.nodeType == CDATA_SECTION_NODE )
		return node.nodeValue;
	else if ( node.nodeType == ELEMENT_NODE )
	{
		var s = "";
		for ( var i = 0;  i < node.childNodes.length;  ++i )
			s += getNodeText( node.childNodes[ i ] );
		return s;
	}
}

/*
 * Remove a class from the set of class names on an element
 */
function removeClass( element, name )
{
	if ( null == element.className )
		return;
	var classNames = element.className.split( ' ' );
	var newClassNames = "";
	for ( var i = 0;  i < classNames.length;  ++i )
	{
		if ( classNames[ i ] != name )
			newClassNames += ' ' + classNames[ i ];
	}
	if ( newClassNames.charAt( 0 ) == ' ' )
		newClassNames = newClassNames.substring( 1 );
	element.className = newClassNames;
}

/*
 * Add a class from the set of class names on an element (or do nothing if already present)
 */
function addClass( element, name )
{
	if ( null == element.className )
		element.className = name;
	else
	{
		var classNames = element.className.split( ' ' );
		var newClassNames = "";
		for ( var i = 0;  i < classNames.length;  ++i )
			if ( classNames[ i ] == name )
				return;
		element.className += ' ' + name;
	}
}

/*
 * Recursively remove markup tags of a given name and/or class
 * tagName or className can be null to indicate any tag or class
 * Note that this is an HTML implementation:  tag name comparisons are case-insensitive (ack!)
 * Originally written to strip annotation highlights.
 */
function stripMarkup( node, tagName, className )
{
	var child = node.firstChild;
	while ( child != null )
	{
		var nextChild = child.nextSibling;
		// only interested in element nodes
		if ( child.nodeType == ELEMENT_NODE )
		{
			this.stripMarkup( child, tagName, className );
			if ( ( tagName == null || child.tagName.toUpperCase( ) == tagName.toUpperCase( ) )
				&& ( className == null || hasClass( child, className ) ) )
			{
				var newChildren = new Array();
				for ( var j = 0;  j < child.childNodes.length;  ++j )
					newChildren[ j ] = child.childNodes[ j ];
				for ( var j = 0;  j < newChildren.length;  ++j )
				{
					child.removeChild( newChildren[ j ] );
					node.insertBefore( newChildren[ j ], child );
				}
				clearEventHandlers( child, false );
				node.removeChild( child );
			}
		}
		child = nextChild;
	}
}

/*
 * Recursively remove markup tags of a given name and/or class
 * tagName or className can be null to indicate any tag or class
 * Note that this is an HTML implementation:  tag name comparisons are case-insensitive (ack!)
 * Originally written to strip annotation highlights.
 */
function stripSubtree( node, tagName, className )
{
	var child = node.firstChild;
	while ( child != null )
	{
		var nextChild = child.nextSibling;
		// only interested in element nodes
		if ( child.nodeType == ELEMENT_NODE )
		{
			this.stripSubtree( child, tagName, className );
			if ( ( tagName == null || child.tagName.toUpperCase( ) == tagName.toUpperCase( ) )
				&& ( className == null || hasClass( child, className ) ) )
			{
				clearEventHandlers( child, true );
				node.removeChild( child );
			}
		}
		child = nextChild;
	}
}

/*
 * Fix the height of an element.  This is necessary for browsers that fail to obey
 * height: 100% correctly (are you listening IE?).
 */
function makeFullHeight( element )
{
	var height = element.parentNode.offsetHeight;
	element.style.height = element.parentNode.offsetHeight + 'px';
}

/*
 * Return the node offset as a measurement from a parent reference node
 */
function getElementYOffset( node, parent )
{
	if ( node == null )
		return 0;
	else if ( node.offsetParent == null )
		return getElementYOffset( node.parentNode, parent );
	else if ( node.offsetParent == parent )
		return node.offsetTop;
	else
		return node.offsetTop + getElementYOffset( node.offsetParent, parent );
}

function getElementXOffset( node, parent )
{
	if ( node.offsetParent == parent )
		return node.offsetLeft ;
	else
		return node.offsetLeft + getElementXOffset( node.offsetParent, parent );
}

/*
 * Get the current window scroll position
 */
function getWindowYScroll( )
{
	if ( window.pageYOffset )
		return window.pageYOffset;
	else if ( document.documentElement && document.documentElement.scrollTop )
		return document.documentElement.scrollTop;
	else if ( document.body )
		return document.body.scrollTop;
}

function getWindowXScroll( )
{
	if ( window.pageXOffset )
		return window.pageXOffset;
	else if ( document.documentElement && document.documentElement.scrollLeft )
		return document.documentElement.scrollLeft;
	else if ( document.body )
		return document.body.scrollLeft;
}

/*
 * Delay for a brief time
 * This is a busy wait, so it's very bad.  I use it for some testing, because
 * browsers may not yet have caught up with some DOM changes, and I need to
 * exclude that as a cause for problems.
 */
function briefPause( ms ) 
{
	date = new Date();
	var curDate = null;
	while ( curDate - date < ms )
		curDate = new Date( );
}

// Test whether a mouseout event really means the mouse left an element
function testMouseLeave( e, element )
{
	dump( "leave " );
	if ( ! e )
		var e = window.event;
	var target = (window.event) ? e.srcElement : e.target;
	// if (tg.nodeName != 'DIV') return;
	if ( target != element)
	{
		dump( "target (" + target + ") != element (" + element + ")\n" );
		return false;
	}
	var related = (e.relatedTarget) ? e.relatedTarget : e.toElement;
	while ( related != target && null != related )
		related = related.parentNode;
	dump( related == target ? "related == target\n" : "left\n\n" );
	return related != target;
}

/*
 * Normalize an element and its children
 * This applies the DOM normalize function, which combines adjacent text nodes
 * It also collapses multiple whitespace characters into a single space.  This
 * is necessary because browsers differ on how they calculate string lengths
 * etc.
 *
 * Also, IE has the absolutely horrifying habit of stripping space characters
 * if they a) are the first characters inside an open tag or b) are the first
 * characters following a closing tag.  In other words, "<span> one </span> two"
 * becomes "<span>one </span>two".  But it doesn't do it all the time;  I haven't
 * yet determined the pattern.  Perhaps there's a standard somewhere that says
 * this is correct display behavior (though if you ask me that doesn't excuse
 * lying about the document).  Collapsing multiple spaces makes good sense in the
 * context of HTML, but trying to handle this look to me a whole lot like data
 * corruption.  So explorer's offsets will differ under some rare circumstances.
 * Exploder, may thy days be numbered and may fire be the eternal rest of thy soul.
 */
function normalizeSpace( node )
{
	portableNormalize( node );
	
// Don't do this anymore, for two reasons:  first, it modifies the page content
// unnecessarily; second, Gecko considers nbsp to be a space character, while
// IE does not.
//	normalizeSpaceRecurse( node );
}

function normalizeSpaceRecurse( node )
{
	for (var i = 0; i < node.childNodes.length; i++ )
	{
		var childNode = node.childNodes[ i ];
		if ( TEXT_NODE == childNode.nodeType )
		{
			childNode.nodeValue = childNode.nodeValue.replace( /(\s)\s+/g, '$1' );
			// See comment at the start of this function about why the following
			// perverted logic has been removed.
			//if ( null == childNode.previousSibling || ELEMENT_NODE == childNode.previousSibling.nodeType )
			//	childNode.nodeValue = childNode.nodeValue.replace( /^\s/, '' );
		}
		if ( ELEMENT_NODE == childNode.nodeType )
			normalizeSpaceRecurse( childNode )
	}
}

/*
 * An implementation of the W3C DOM normalize function for IE
 * IE often crashes when its implementation is called
 * I'm not going to bother implementing CDATA support
 */
function portableNormalize( node )
{
	// Internet Explorer often crashes when it tries to normalize
	if ( 'exploder' != detectBrowser( ) )
		node.normalize( );
	else
	{
		if ( ELEMENT_NODE != node.nodeType )
			return;
		var child = node.firstChild;
		var next;
		while ( null != child )
		{
			if ( ELEMENT_NODE == child.nodeType )
			{
				portableNormalize( child );
				child = child.nextSibling;
			}
			else if ( TEXT_NODE == child.nodeType )
			{
				if ( '' == child.nodeValue )
				{
					next = child.nextSibling; 
					child.parentNode.removeChild( child );
				}
				else
				{
					next = child.nextSibling;
					var s = '';
					while ( null != next && TEXT_NODE == next.nodeType )
					{
						s += next.nodeValue;
						var t = next.nextSibling;
						child.parentNode.removeChild( next );
						next = t;
					}
					if ( '' != s )
					{
						// this means there was more than one text node in sequence
						child.nodeValue = child.nodeValue + s;
					}
				}
				child = next;
			}
			else
				child = child.nextSibling;
		}
	}
}


/*
 * Browser detects are bad.
 * However, this is needed because IE simply can't handle some things (it crashes)
 * The only value I care about is IE, so this function only returns "opera", "exploder", or "other"
 */
function detectBrowser( )
{
	var agent = navigator.userAgent.toLowerCase()
	if ( -1 != agent.indexOf( 'opera' ) )  return "opera";  // opera masquerades as ie, so check for it first
	else if ( -1 != agent.indexOf( 'msie' ) )  return "exploder";
	else return "other";
}

/*
 * Walk through nodes in document order
 */
function DOMWalker( startNode )
{
	this.node = startNode;
	this.endTag = false;
}

DOMWalker.prototype.destroy = function( )
{
	this.node = null;
}

DOMWalker.prototype.walk = function( gointo )
{
	if ( this.endTag || ELEMENT_NODE != this.node.nodeType || ! gointo )
	{
		if ( this.node.nextSibling )
		{
			this.node = this.node.nextSibling;
			this.endTag = false;
		}
		else
		{
			this.node = this.node.parentNode;
			this.endTag = true;
		}
	}
	else // ( ELEMENT_NODE == this.node.nodeType && gointo )
	{
		if ( this.node.firstChild )
			this.node = this.node.firstChild;
		else
			this.endTag = true;
	}
	return null == this.node ? false : true;
}


/*
 * Return the next node after the current one while walking
 * I'm wrying to replace this with the DOMWalker
 */
function walkNextNode( node, fskip )
{
	var next = node;
	do
	{
		if ( ELEMENT_NODE == next.nodeType && next.firstChild && ( null == fskip || ! fskip( next ) ) )
		{
			trace( 'node-walk', 'walkNextNode (' + node + '=' + node.nodeValue + ') child' );
			next = next.firstChild;
		}
		else if ( next.nextSibling )
		{
			trace( 'node-walk', 'walkNextNode (' + node + '=' + node.nodeValue + ') sibling' );
			next = next.nextSibling;
		}
		else
		{
			trace( 'node-walk', 'walkNextNode (' + node + '=' + node.nodeValue + ') parent' );
			next = next.parentNode;
			while ( null != next && null == next.nextSibling )
				next = next.parentNode;
			if ( null != next )
				next = next.nextSibling;
		}
	}
	while ( null != next && fskip && fskip( next ) );
	trace( 'node-walk', "walkNextNode (" + node + "=" + node.nodeValue + " -> " + next + " (" + next.nodeValue + ")");
	return next;
}

/*
 * Walk r forward until len characters have been passed
 * r.container - the current container element
 * r.offset = the offset within the node to start looking
 */
function walkUntilLen( node, len )
{
	while ( node != null)
	{
		if ( TEXT_NODE == node.nodeType || CDATA_SECTION_NODE == node.nodeType )
		{
			if ( len <= node.length )
			{
//				var parent = node.parentNode;
				var result = new Object();
				result.container = node; //parent;
				result.offset = len;
				// Now figure out where this is in the context of the parent element
//				for ( var child = parent.firstChild;  child != node;  child = child.nextSibling )
//					result.offset += nodeTextLength( child, null );
				return result;
			}
			else
			{
				len -= node.length;
				node = walkNextNode( node, null );
			}
		}
		else
			node = walkNextNode( node, null );
	}
	return null;
}

function clearEventHandlers( element, recurse )
{
	element.onmousedown = null;
	element.onmouseup = null;
	element.onkeydown = null;
	element.onkeypress = null;
	element.onkeyup = null;
	element.onmouseover = null;
	element.onmouseout = null;
	element.onfocus = null;
	element.onblur = null;
	element.onclick = null;

	if ( recurse )
	{
		for ( var child = element.firstChild;  null != child;  child = child.nextSibling )
		{
			if ( ELEMENT_NODE == child.nodeType )
				clearEventHandlers( child, true );
		}
	}
}

function clearObjectRefs( element, fields )
{
	if ( isString( fields ) )
		delete element[ fields ];
	else
	{
		for ( var i = 0;  i < fields.length;  ++i )
			delete element[ fields[ i ] ];
	}
	for ( var child = element.firstChild;  null != child;  child = child.nextSibling )
	{
		if ( ELEMENT_NODE == child.nodeType )
			clearObjectRefs( child, fields );
	}
}

function isString( s )
{
	if ( typeof( s ) == 'string' )
		return true;
	else if ( typeof( s ) == 'object' )
		// Based on Kas Thomas's analysis:
		return null != s.constructor.toString( ).match( /string/i );
	else
		return false;
}
