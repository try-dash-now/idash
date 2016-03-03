proc check_status {} {
	set root [ixNet getRoot]
	set traffic $root/traffic
	return [ixNet getAttr $traffic -state]
}

proc stop_traffic {} {
	set root [ixNet getRoot]
	set traffic $root/traffic
	return [ixNet exec stop $traffic]
}

proc start_traffic {} {
	set root [ixNet getRoot]
	set traffic $root/traffic
	return [ixNet exec start $traffic]
}

proc clear_stats {} {
	ixNet exec clearStats
}
#ryi7/16/2015begin

proc ixNetApplyTraffic {} {
    ixNet setAttribute [ixNet getRoot]traffic -refreshLearnedInfoBeforeApply true
    ixNet commit
    update idletasks
    after 5000
	update idletasks
    if {[catch [ixNet exec apply [ixNet getRoot]traffic] msg]} {
        puts "Apply traffic successful!"
    } else {
        puts "Failed to apply traffic, $msg"
    }
    after 10000
}
#ryi7/16/2015end

proc generate_traffic {} {
	#it may take a long time to start all protocols
	ixNet exec startAllProtocols
	set root [ixNet getRoot]
	set traffic $root/traffic
	# get traffic items
	set traffic_item_list [ixNet getList $traffic trafficItem]
	set res {}
	foreach traffic_item $traffic_item_list {
		lappend res [ixNet exec generate $traffic_item]
	}
	set state [ixNet getAttr $traffic -state]
	return [ixNet exec apply $traffic]
}

# added by speng 7/21/2015 begin
proc apply_traffic {} {
	set root [ixNet getRoot]
	set traffic $root/traffic
	return [ixNet exec apply $traffic]
}

proc get_traffic_items {} {
	set root [ixNet getRoot]
	set traffic $root/traffic
	# get traffic items
	set traffic_item_list [ixNet getList $traffic trafficItem]
	return $traffic_item_list
}

proc regenerate_traffic {} {
	set root [ixNet getRoot]
	set traffic $root/traffic
	# get traffic items
	set traffic_item_list [ixNet getList $traffic trafficItem]
	set res {}
	foreach traffic_item $traffic_item_list {
		lappend res [ixNet exec generate $traffic_item]
	}
	return $res
}

proc ixNetClearAllConfig {} {
    ixNet rollback
    ixNet execute newConfig
    #after 10000
}
# added by speng 7/21/2015 end

proc monitor_flow_statistics {item} {
	#'item' designates the statistics item to monitor
	# ixNet help ::ixNet::OBJ-/statistics
	# ixNet getL ::ixNet::OBJ-/statistics view
	# ixNet getL {::ixNet::OBJ-/statistics/view:"Flow Statistics"} page
	# ixNet help {::ixNet::OBJ-/statistics/view:"Flow Statistics"/page}
	# ixNet getA {::ixNet::OBJ-/statistics/view:"Flow Statistics"/page} -columnCaptions
	# ixNet getA {::ixNet::OBJ-/statistics/view:"Flow Statistics"/page} -totalPages
	#define title_list, the title line
	set title_list [ixNet getA {::ixNet::OBJ-/statistics/view:"Flow Statistics"/page} -columnCaptions]  
	#get the index of item in title_list, item is the arguement passed into this tcl script. It can be {Loss %}, {Tx Frame Rate}, or {Rx Frame Rate} and so on
	set index [lsearch $title_list $item]
	#define value, each element of it is a line containing data
	set value [ixNet getA {::ixNet::OBJ-/statistics/view:"Flow Statistics"/page} -rowValues]
	#the structure of value is {{... ...}} {{... ...}} {{... ...}}
	#so we need "eval {set v} $v" to take off its outer list structure
	#create an empty item list
	set item_list {}
	foreach v $value {
	eval {set v} $v
	lappend item_list [lindex $v $index]
	}
	return $item_list
}

proc set_tcl_env {IxTclNetwork_path host_ip version} {
	#lappend auto_path "C:/Program Files/Ixia/IxNetwork/6.20-EA/TclScripts/Lib/IxTclNetwork"
	global auto_path
	lappend auto_path $IxTclNetwork_path
	package require IxTclNetwork
	return [ixNet connect $host_ip -port 8009 -version $version]
}

###ryi 7/10/2015 beginning###

proc read_Stats {viewName item} {
	#set title_list [ixNetGetColTitles $viewName]
	#set index [lsearch $titles $item]
	set totalPage [ixNet getA ::ixNet::OBJ-/statistics/view:"$viewName"/page -totalPages]
	set curPage 1
	set item_list []
	set trafficObj ::ixNet::OBJ-/statistics/trafficStatViewBrowser:"$viewName"
	if { [ixNet getAttribute $trafficObj -enabled]  == "false"} {
        ixNet setAttribute $trafficObj -enabled true
        ixNet commit
    }
    while { $curPage <= $totalPage } {
	    ixNet setAttribute $trafficObj -currentPageNumber $curPage
	    ixNet commit
	    set tmp [ readStats $trafficObj $item ]
	    lappend item_list [ lindex $tmp 1 ]
	    #lappend item_list [ readStats $trafficObj $item ]
        incr curPage
	}
	return $item_list
}

proc read_Name {viewName item} {
	set totalPage [ixNet getA ::ixNet::OBJ-/statistics/view:"$viewName"/page -totalPages]
	set curPage 1
	set item_list []
	set trafficObj ::ixNet::OBJ-/statistics/trafficStatViewBrowser:"$viewName"
	if { [ixNet getAttribute $trafficObj -enabled]  == "false"} {
        ixNet setAttribute $trafficObj -enabled true
        ixNet commit
    }
    while { $curPage <= $totalPage } {
	    ixNet setAttribute $trafficObj -currentPageNumber $curPage
	    ixNet commit
	    set tmp [ readStats $trafficObj $item ]
	    lappend name_list [ lindex $tmp 0 ]
	    #lappend name_list [ readStats $trafficObj $item ]
        incr curPage
	}
	return $name_list
}

proc readStats {viewName item} {
# Get snapshot data for the traffic page
    set snapshot [ixNet getAttribute $viewName -snapshotData]
# Get lists of row names, column names, and cell values
    set rowNames [lindex $snapshot 1]
    set colNames [lindex $snapshot 2]
    set allVals [lindex $snapshot 3]
    set colIndex [lsearch $colNames $item]
# end setup that could be cached
    set rowCount [llength $rowNames]
    set list []
# Get data for the specified columns and write them into a CSV file
    for {set rowIndex 0} {$rowIndex < $rowCount} {incr rowIndex} {
        set rowName [lindex $rowNames $rowIndex]
        set rowVals [lindex $allVals $rowIndex]
        set cellVal [lindex $rowVals $colIndex]
        lappend list $cellVal
    }
    return [list $rowNames $list]
}

#ryi 7/29/2015 begin
proc getFlowName {viewName row} {
    set trafficObj ::ixNet::OBJ-/statistics/trafficStatViewBrowser:"$viewName"
    set oldPage 1
    ixNet setAttribute $trafficObj -currentPageNumber $oldPage
    ixNet commit
    set newPage [expr $row / 50 ]
    set curPage [expr $oldPage + $newPage]
    set item_list []
	ixNet setAttribute $trafficObj -currentPageNumber $curPage
	ixNet commit
	set snapshot [ixNet getAttribute $trafficObj -snapshotData]
	set rowNames [lindex $snapshot 1]
	set rowIndex [expr $row % 50]
	set rowList [lindex $rowNames $rowIndex]
	return $rowList
}
#ryi 7/29/2015 end

#ryi 8/4/2015 begin
proc getTrafficName {} {
    set title_list [ixNet getA {::ixNet::OBJ-/statistics/view:"Traffic Item Statistics"/page} -columnCaptions]
    set item "Traffic Item"
	set index [lsearch $title_list $item]
	set value [ixNet getA {::ixNet::OBJ-/statistics/view:"Traffic Item Statistics"/page} -rowValues]
	set item_list []
	foreach v $value {
	    eval {set v} $v
	    lappend item_list [lindex $v $index]
	}
	#package require csv
    #set result [::csv::join $item_list ]
    set result [join $item_list "\n"]
	return $result
	#$item_list
}
#ryi 8/5/2015 end

proc ixNetGetViewPage {viewName} {
    set root [ixNet getRoot]
    set viewList [ixNet getList $root/statistics view]
    set portView [lsearch $viewList ::ixNet::OBJ-/statistics/view:"$viewName"]
    set sg_view [lindex $viewList $portView]
    set viewPage [lindex [ixNet getList $sg_view page] 0]
    return $viewPage
}

proc ixNetGetColTitles {viewName} {
    set viewPage [ixNetGetViewPage $viewName]
    set titles [ixNet getAttri $viewPage -columnCaptions]
    return $titles
}

proc ixNetGetOneRow {viewName rowIndex} {
    set viewPage [ixNetGetViewPage $viewName]
    set row_values [ixNet getAttribute $viewPage -rowValues]
    set one_rowList [lindex $row_values $rowIndex]
    set one_row [lindex $one_rowList 0]
    return $one_row
}

proc ixNetCheckTrafficItemElement {row colum} {
    set viewName "Flow Statistics"
    set rownum [IxNetwork::ixNetGetOneRow $viewName $row]
    set value [lindex $rownum $colum]
    puts $value
}


###ryi 7/10/2015 end###

###ryi 7/16/2015begin 
proc ixNetStartAllProtocols {} {
    if { [catch [ixNet exec startAllProtocols] msg] } {
        puts "Start all protocols successful!"
        return 0
    } else {
        puts "Failed Start all protocols!"
    }
}

proc ixNetCheckProtocolSum {} {
    set viewName "Protocol Summary"
    set row [IxNetwork::ixNetGetOneRow $viewName 0]
    set name [lindex $row 0]
    set sessionInit [lindex $row 1]
    set sessionsucc [lindex $row 2]
    set sessionfail [lindex $row 3]
    if {$sessionInit == $sessionsucc && $sessionfail == 0} {
        puts Passed
    }
}

proc ixNetStopAllProtocols {} {
    if {[catch [ixNet exec stopAllProtocols] msg]} {
    puts "Stop all protocols successful!"
    } else {
        puts "failed stop all protocols!"
    }
    after 12000
}
###ryi 7/16/2015 end

### added by speng 7/16/2015 beginning
proc ixNetLoadIxncfgFile {confFile } {
    ixNetClearAllConfig
    catch {ixNet exec loadConfig [ixNet readFrom $confFile]} tmpresult

    if {[string match *OK $tmpresult]} {
        #puts "Load configuration file is successful! $confFile"
    } else {
        puts "Load configuration file is failed, $confFile. said: $tmpresult"
        return 1
    }
    #after 15000

    set v ""
    foreach v [ixNet getList [ixNet getRoot] vport] {
    	puts "vport($v) - [ixNet getA $v -assignedTo]"
    }

    if { $v == "" } {
     	puts "Load configuration file is failed, $confFile. said: $tmpresult"
    	return 1
    }

    #wait for last vport to be up.
    for { set i 0 } { $i < 30 } { incr i 1 } {
    	set res [ixNet getA $v -state]
    	if { $res == "up" } { break }
    	after 1000
    }
	catch {
		ixTclNet::ClearOwnershipForAllPorts
		ixTclNet::ConnectPorts
	}
	#puts "Load configuration file is successful! $confFile"
	return 0
}

proc ixNetClearAllConfig {} {
    ixNet rollback
    ixNet execute newConfig
    #after 10000
}
### added by speng 7/16/2015 end