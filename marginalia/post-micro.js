/*
 * post-micro.js
 * Part of Marginalia web annotation
 * See www.geof.net/code/annotation/ for full source and documentation.
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
 * Support for message / blog post micro-format.  Because there is as-yet no standard,
 * this is my own format.  It should change to match established practice once there
 * is such a thing.
 */

// These class names will change once there's a microformat standard.
PM_POST_CLASS = 'hentry';				// this is an addressable fragment for annotation
PM_CONTENT_CLASS = 'entry-content';	// the content portion of a fragment
PM_TITLE_CLASS = 'entry-title';		// the title of an annotated fragment
PM_AUTHOR_CLASS = 'author';			// the author of the fragment
PM_DATE_CLASS = 'published';			// the creation/modification date of the fragment
PM_URL_REL = 'bookmark';				// the url of this fragment (uses rel rather than class attribute)

/*
 * This class keeps track of PostMicro stuff on a page
 * Initially that information was integrated into individual DOM nodes (especially
 * as PostMicro objects), but because of memory leak problems I'm moving it here.
 */
function PostPageInfo( )
{
	this.posts = new Array( );
	this.postsById = new Object( );
	this.postsByUrl = new Object( );
	this.IndexPosts( document.documentElement );
	return this;
}

PostPageInfo.prototype.IndexPosts = function( root )
{
	var posts = getChildrenByTagClass( root, null, PM_POST_CLASS );
	for ( var i = 0;  i < posts.length;  ++i )
	{
		var postElement = posts[ i ];
		var post = new PostMicro( postElement );
		this.posts[ this.posts.length ] = post;
		if ( null != posts[ i ].id && '' != posts[ i ].id )
			this.postsById[ posts[ i ].id ] = post;
		if ( null != post.url && '' != post.url )
			this.postsByUrl[ post.url ] = post;
		postElement.post = post;
	}
}

PostPageInfo.prototype.getPostById = function( id )
{
	return this.postsById[ id ];
}

PostPageInfo.prototype.getPostByUrl = function( url )
{
	return this.postsByUrl[ url ];
}


/*
 * For ignoring post content when looking for specially tagged nodes, so that authors
 * of that content (i.e. users) can't mess things up.
 */
function _skipPostContent( node )
{
	return ( ELEMENT_NODE == node.nodeType && hasClass( node, PM_CONTENT_CLASS ) );
}


/*
 * Post Class
 * This is attached to the root DOM node of a post (not the document node, rather the node
 * with the appropriate class and ID for a post).  It stores references to child nodes
 * containing relevant metadata.  The class also provides a place to hang useful functions,
 * e.g. for annotation or smart copy support.
 */
function PostMicro( element)
{
	// Point the post and DOM node to each other
	this.element = element;

	// The title
	var metadata = getChildByTagClass( element, null, PM_TITLE_CLASS, _skipPostContent );
	this.title = metadata == null ? '' : getNodeText( metadata );
	
	// The author
	metadata = getChildByTagClass( element, null, PM_AUTHOR_CLASS, _skipPostContent );
	this.author = metadata == null ? '' : getNodeText( metadata );
	
	// The date
	metadata = getChildByTagClass( element, 'abbr', PM_DATE_CLASS, _skipPostContent );
	if ( null == metadata )
		this.date = null;
	else
	{
		var s = metadata.getAttribute( 'title' );
		if ( null == s )
			this.date = null;
		else
		{
			var matches = s.match( /(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})[+-](\d{4})/ );
			if ( null == matches )
				this.date = null;
			else
				// I haven't figured out how to deal with the time zone, so it assumes that server
				// time and local time are the same - which is rather bad.
				this.date = new Date( matches[1], matches[2]-1, matches[3], matches[4], matches[5] );
		}
	}
	
	// The node containing the url
	metadata = getChildAnchor( element, PM_URL_REL, _skipPostContent );
	this.url = metadata.getAttribute( 'href' );
	
	// The node containing the content
	// Any offsets (e.g. as used by annotations) are from the start of this node's children
	this.contentElement = getChildByTagClass( this.element, null, PM_CONTENT_CLASS, _skipPostContent );

	return this;
}

/*
 * Accessor for related element
 * Used so that we can avoid storing a pointer to a DOM node,
 * which tends to cause memory leaks on IE.
 */
PostMicro.prototype.getElement = function( )
{
	return this.element;
}


/*
 * Accessor for content element
 * Used so that we can avoid storing a pointer to a DOM node,
 * which tends to cause memory leaks on IE.
 */
PostMicro.prototype.getContentElement = function( )
{
	return getChildByTagClass( this.element, null, PM_CONTENT_CLASS, _skipPostContent );
}

function getPostMicro( element )
{
	if ( ! element.post )
		element.post= new PostMicro( element );
	return element.post;
}

function findPostByUrl( url )
{
	var fragments = new Array( );
	getChildrenByTagClass( document.documentElement, null, PM_POST_CLASS, fragments, _skipPostContent );
	for ( var i = 0;  i < fragments.length;  ++i )
	{
		urlNode = getChildAnchor( fragments[ i ], PM_URL_REL, _skipPostContent );
		// IE returns the absolute URL, not the actual content of the href field
		// (i.e., the bloody piece of junk lies).  So instead of straight equality,
		// I need to test whether the endings of the two URLs match.  In rare
		// cases, this might cause a mismatch.  #geof#
		var href = urlNode.getAttribute( 'href' );
		if ( null != urlNode && href.length >= url.length && href.substring( href.length - url.length ) == url )
			return getPostMicro( fragments[ i ] );
	}
	return null;
}

