#############################################################################################
#
# AvailableHardwareUtils.tcl  -
#
# Copyright © 1997-2006 by IXIA.
# All Rights Reserved.
#
#
#############################################################################################

########################################################################################
# Procedure: ixTclPrivate::connectToChassis
#
# Description: Attempts to connect to all chassis given in the list
#
# Arguments: chassisList - A list of chassis names
#						- timeoutCount: In seconds. When to give up if could not connect to all chassis
#
# Returns: A return code of 0 for success and 1 for error.
########################################################################################


proc ::ixTclNet::ConnectToChassis { hostnameList {timeoutCount 1000}} {

	set retCode 1

	#remove duplicates
	set index 0
    set newHostnameList {}
	while {[llength $hostnameList] > 0} {
		set trimVal [lindex $hostnameList $index]
        lappend newHostnameList $trimVal
        set hostnameList [lreplace $hostnameList $index $index]
		set matches [lsearch $hostnameList $trimVal]
   
		while {$matches > 0 } {
			set hostnameList [lreplace $hostnameList $matches $matches]
            set matches [lsearch $hostnameList $trimVal] 
		}  
	}
	
    set hostnameList $newHostnameList

	set root [ixNet getRoot]

	#AvailableHardware is a required node so there is only one item in the list.
	set availHwId [lindex [ixNet getList $root availableHardware] 0]
    
	#If the chassis is aready connected don't bother connecting again.
	#Remove connected chassis from the list.
	set chassisList [ixNet -timeout 0 getList $availHwId chassis]

	foreach chassisId $chassisList {
		set chassisIp [ixNet getAttr $chassisId -hostname]
		set connected [ixNet getAttr $chassisId -state]
		
		if {$connected == "ready"} {
			set ipIndex [lsearch $hostnameList $chassisIp] 
			if {$ipIndex != -1} {
				set hostnameList [lreplace $hostnameList $ipIndex $ipIndex]
			}
		}
	}

	if {[llength $hostnameList] == 0} {
		#puts "All Chassis in the list already connected..."
		set retCode 0
		return $retCode
	}
	#puts "connecting to $hostnameList"

	ixNet -timeout 0 add $availHwId chassis -hostname $hostnameList
	ixNet -timeout 0 commit

	set chassisList [ixNet getList $availHwId chassis]
	
	foreach hostname $hostnameList {
		foreach chassisId $chassisList {
			set chassisIp [ixNet getAttr $chassisId -hostname]
			if {$chassisIp == $hostname} {
				set hostnameIdArray($hostname) $chassisId
				break
			}
		}
	}
	#puts "arry = [array get hostnameIdArray]"

	foreach {hostname chassisId} [array get hostnameIdArray] {
		if {[ixNet getAttribute $chassisId -state] == "ready"} {
			unset hostnameIdArray($hostname)
		}
	}

	set waitCount 1

	while {[array size hostnameIdArray] > 0 && $waitCount < $timeoutCount} {
		after 1000

		foreach {hostname chassisId} [array get hostnameIdArray] {
			if {[ixNet getAttribute $chassisId -state] == "ready"} {
				unset hostnameIdArray($hostname)
			}
		}
        incr waitCount
	}

	if {[array size hostnameIdArray] == 0} {
		set retCode 0
	} else {
		set notConnectedList {}
		foreach {hostname chassisId} [array get hostnameIdArray] {
			lappend  notConnectedList $hostname
		}
		error "Could not connect to the following hosts: $notConnectedList"
	}
	return $retCode
}



########################################################################################
#  Procedure  :  CreatePortListWildCard
#
#  Description:  This commands creates a list of ports in a sorted order based on the
# physical slots. It accepts * as a wild card to indicate all cards or all ports on a
# card. A wild card cannot be used for chassis IP. Also, if a combination of a list
# element containing wild cards and port numbers are passed, then the port list passed
# MUST be in a sorted order, otherwise the some of those ports might not make it in the
# list. For example,
# CreatePortListWildCard {1 * *} - all cards and all ports on chassis 1
# CreatePortListWildCard {{1 1 *} {1 2 1} { 1 2 2}} - all ports on card 1 and
#                           ports 1 and 2 on card 2.
#
#  Arguments  :
#      portList         - Represented in Chassis Card Port and can be a list also
#      excludePorts     - exclude these ports from the sorted port list
#
########################################################################################
proc ::ixTclNet::CreatePortListWildCard {portList {excludePorts {}}} \
{
    set retList {}

    # If excludePorts is passed as a single list, then put braces around it
    if {[llength $excludePorts] == 3 && [llength [lindex $excludePorts 0]] == 1} {
        set excludePorts [list $excludePorts]
    }

    foreach portItem $portList {
        scan [join [split $portItem ,]] "%s %s %s" ch fromCard fromPort
    
        set origFromPort    $fromPort

        if { $ch == "*"} {
            puts "Error: Chassis IP cannot be a wildcard. Enter a valid number"
            return $retList
        }

        set chassisObjRef  [::ixTclNet::GetRealPortObjRef $ch]

        set maxCardsInChassis   [llength [ixNet getList  $chassisObjRef card]]
        if { $fromCard == "*"} {
            set fromCard 1
            set toCard   $maxCardsInChassis
        } else {
            set toCard   $fromCard
        }

        for {set l $fromCard} {$l <= $toCard} {incr l} {
            set cardObjRef  [::ixTclNet::GetRealPortObjRef $ch $l]

            set maxPorts    [llength [ixNet getList  $cardObjRef port]]

            if { $origFromPort == "*"} {
                set fromPort 1
                set toPort   $maxPorts
            } else {
                set toPort   $fromPort
            }

            for {set p $fromPort} {$p <= $toPort} {incr p} {
                set portObjRef  [::ixTclNet::GetRealPortObjRef $ch $l $p]

                if {[lsearch $excludePorts "$ch $l $p"] == -1 && [lsearch $retList "$ch $l $p"] == -1} {
                    lappend retList [list $ch $l $p]
                }

            }
        }
    }

    return $retList
}


########################################################################################
# Procedure: ixTclPrivate::GetRealPortObjRef
#
# Description: Returns objRef for the specified real port
#
# Arguments: hostname1 cardNumber portNumber
#                       
#                         
# Returns: Return port objRef or null if it fails.
########################################################################################


proc ::ixTclNet::GetRealPortObjRef { hostname {cardId 0} {portId 0}} {

    set root [ixNet getRoot]
	set availHwId [lindex [ixNet -timeout 0 getList $root availableHardware] 0]
	set chassisList [ixNet -timeout 0 getList $availHwId chassis]

    set chassisRef ""

    
	foreach chassisItem $chassisList {
		set chassisIp [ixNet getAttr $chassisItem -hostname]
		if {$chassisIp == $hostname} {
			set chassisRef $chassisItem
			break
		}
	}
	if {$cardId == 0} {
        return $chassisRef
    }


    set cardRef ""
    if {$chassisRef != ""} {
        set cardList [ixNet -timeout 0 getList $chassisRef card]

        foreach cardItem $cardList {
            set id [ixNet getAttribute $cardItem -cardId]
            if {$id == $cardId} {
			    set cardRef $cardItem
			    break
            }
		}

        if {$portId == 0} {
            return $cardRef
        }
          
        set portRef ""
        if {$cardRef != ""} {
            set portList [ixNet -timeout 0 getList $cardRef port]

            foreach portItem $portList {
                set tempId [ixNet getAttr $portItem -portId]
                if {$tempId == $portId} {
			        set portRef $portItem
			        break
                } 
            }
        }

    }
    return $portRef
}

