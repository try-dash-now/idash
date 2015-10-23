#############################################################################################
#
# pkgIndex.tcl
#
# Copyright © 1997-2006 by IXIA.
# All Rights Reserved.
#
#
#############################################################################################

if {[lsearch [package names] IxTclNetwork] != -1} {
	return
}

set env(IXTCLNETWORK_LOCATION) [file dirname [info script]]
if {[lsearch ::auto_path $env(IXTCLNETWORK_LOCATION)] == -1} {
	lappend ::auto_path $env(IXTCLNETWORK_LOCATION)
}

package ifneeded IxTclNetwork 6.20.601.18 {
	package provide IxTclNetwork 6.20.601.18

	namespace eval ::ixTclNet {}
	namespace eval ::ixTclPrivate {}

	foreach fileItem1 [glob -nocomplain $env(IXTCLNETWORK_LOCATION)/Generic/*.tcl] {
		if {![file isdirectory $fileItem1]} {
			source  $fileItem1
		}
	}

	source [file join $env(IXTCLNETWORK_LOCATION) IxTclNetwork.tcl]
}
