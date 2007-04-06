/* 
 * Logging code
 */

// Only works on Mozilla - other browsers have no dump function
function logError( s )
{
	if ( LOGGING_ON )
	{
		if ( window.dump )
		{
			// Not working - dunno why.  Or why it has to be so obtuse.
			/*
			netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
			var logger = Components.classes["@mozilla.org/consoleservice;1"].getService(Components.interfaces.nsIConsoleService);
			logger.logStringMessage( s  );
			*/
			dump( "ERROR: " + s + "\n" );
		}
		var dumpElement = document.getElementById( 'debug' );
		if ( INWINDOW_LOG && dumpElement )
		{
			dumpElement.style.display = 'block';
			var li = document.createElement( 'li' );
			li.appendChild( document.createTextNode( s ) );
			dumpElement.appendChild( li );
		}
	}
}

function setTrace( topic, b )
{
	if ( null == window.traceSettings )
		window.traceSettings = new Object( );
	window.traceSettings[ topic ] = b;
}

function trace( topic, s )
{
	if ( TRACING_ON && !topic || ( null != window.traceSettings && window.traceSettings[ topic ]) )
	{
		if ( window.dump )
			dump( s + "\n");
		var dumpElement = document.getElementById( 'debug' );
		if ( INWINDOW_LOG && dumpElement )
		{
			dumpElement.style.display = 'block';
			var li = document.createElement( 'li' );
			li.appendChild( document.createTextNode( s ) );
			dumpElement.appendChild( li );
		}
	}
}
