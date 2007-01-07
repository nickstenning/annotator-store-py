/*
 * static-annotate.js
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
 
SERVICE_PATH = "example-annotations.xml";

/*
 * Initialize the REST annotation service
 */
function AnnotationService( wwwroot, user )
{
	this.current_id = 1000; 
	return this;
}

/*
 * Fetch a list of annotations from the server
 */
AnnotationService.prototype.listAnnotations = function ( url, f )
{
	var xmlhttp = createAjaxRequest( );
	xmlhttp.open( 'GET', SERVICE_PATH );
	xmlhttp.onreadystatechange = function( ) {
		if ( 4 == xmlhttp.readyState ) {
			if ( 200 == xmlhttp.status ) {
				if ( null != f )
				{
					f( xmlhttp.responseXML );
				}
			}
			else {
				logError( "AnnotationService.listAnnotations failed with code " + xmlhttp.status );
			}
			xmlhttp = null;
		}
	}
	trace( 'annotation-service', "AnnotationService.listAnnotations " + SERVICE_PATH)
	xmlhttp.send( null );
}

/*
 * Create an annotation on the server
 */
AnnotationService.prototype.createAnnotation = function( url, offset, length, note, access, quote, quote_title, quote_author, f )
{
	this.current_id += 1;
	if ( null != f )
		f( SERVICE_PATH + '/' + this.current_id );
}

/*
 * Update an annotation on the server
 */
AnnotationService.prototype.updateAnnotation = function( annotationId, note, access, f )
{
	if ( null != f )
		f( null );
}

/*
 * Delete an annotation on the server
 */
AnnotationService.prototype.deleteAnnotation = function( annotationId, f )
{
	if ( null != f )
		f( null );
}

