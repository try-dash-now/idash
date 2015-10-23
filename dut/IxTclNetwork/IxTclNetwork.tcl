#############################################################################################
#
# IxTclNetwork.tcl  - required file for package require IxTclNetwork
#
# Copyright 1997-2006 by IXIA.
# All Rights Reserved.
#
#
#############################################################################################

namespace eval ::IxNet {
	variable commandPatterns {getRoot getNull help connect disconnect setSessionParameter getVersion add commit readFrom writeTo exec* setA* setM*}
	variable _isClientTcl true
	variable _debugFlag false
	variable _ipAddress {}
	variable _port {}
	variable _tclResult {}
	variable _evalResult {}
	variable _socketId {}
	variable _OK {::ixNet::OK}
	variable _buffer {}
	variable STARTINDEX "<"
	variable STOPINDEX ">"
	variable STX "001"
	variable IXNET "002"
	variable RESPONSE "003"
	variable EVALRESULT "004"
	variable READFROM "005"
	variable WRITETO "006"
	variable FILENAME "007"
	variable FILECONTENT "008"
	variable CONTENT "009"
	variable TCL_OK 0
	variable TCL_ERROR 1
	variable BIN2 [binary format "c" 2]
	variable BIN3 [binary format "c" 3]

	proc SetDebug {debugFlag} {
		variable _debugFlag

		set _debugFlag $debugFlag
	}
	proc SetDefaultSocketModes {} {
		variable _socketId

		if {$_socketId != ""} {
			fconfigure $_socketId -buffersize 131072 -buffering none -translation binary -blocking true -encoding binary
		}
	}
	proc Connect {ipAddress port ixNetCommand} {
		variable _ipAddress
		variable _port
		variable _socketId
		variable _OK

		if {$_socketId != ""} {
			set socketError [fconfigure $_socketId -error]

			if {$socketError != ""} {
				Close
			}
		}

		if {$_socketId == ""} {
			set _ipAddress $ipAddress
			set _port $port
			set _socketId [socket $_ipAddress $_port]

			::IxNet::SetDefaultSocketModes

			set serverTclPort [::IxNet::GetTclResult]

			return [SendBuffer $ixNetCommand]
		} else {
			set addressOk false
			set portOk false
			set peerDetails [fconfigure $_socketId -peername]
			lappend peerDetails $_ipAddress
			foreach {element} $peerDetails {
				if {[string first $ipAddress $element] == 0} {
					set addressOk true
				}
				if {[string first $port $element] == 0} {
					set portOk true
				}
			}
			if {$addressOk && $portOk} {
				return $_OK
			}
			puts "Cannot connect to $ipAddress:$port as a connection is already established to $peerDetails"; update
		}
	}
	proc Close {} {
		if {$::IxNet::_socketId != ""} {
			catch {close $::IxNet::_socketId}
			set ::IxNet::_ipAddress {}
			set ::IxNet::_port {}
			set ::IxNet::_socketId {}
			set ::IxNet::_evalResult 1
			set ::IxNet::_tclResult "connection closed"
			set ::IxNet::_receiveReady true
			update
		}
	}
	proc Disconnect {command} {
		variable _socketId

		set response [::IxNet::Send $command]

		::IxNet::Close

		return $response
	}
	proc ThrowError {} {
		set errorMessage $::errorInfo

		::IxNet::Close

		error $errorMessage
	}
	proc CheckConnection {} {
		variable _socketId

		if {$_socketId != ""} {
			set socketError [fconfigure $_socketId -error]

			if {$socketError != ""} {
				Close
				error "not connected ($socketError)"
			}
		} else {
			error "not connected"
		}
	}
	proc Send {command} {
		variable _debugFlag
		variable _socketId
		variable STX
		variable IXNET
		variable CONTENT

		CheckConnection

		if {$_socketId != ""} {
			if {$_debugFlag} {
				puts "::IxNet::Send=<$STX><$IXNET><$CONTENT[string length $command]>$command"; update
			}

			if {[catch {puts -nonewline $_socketId "<$STX><$IXNET><$CONTENT[string length $command]>$command"} errorMessage]} {
				Close
				if {[string first "connection reset by peer" $errorMessage] != -1} {
					error "connection reset by peer"
				} else {
					error $errorMessage
				}
			}

			flush $_socketId

			return [::IxNet::GetTclResult]

		} else {
			error "not connected"
		}
	}
	proc Read {} {
		variable _tclResult
		variable _evalResult
		variable _debugFlag
		variable _socketId
		variable STARTINDEX
		variable STOPINDEX
		variable STX
		variable EVALRESULT
		variable RESPONSE
		variable TCL_OK
		variable TCL_ERROR
		set filename ""

		# read to the stop index
		# read the content length
		while {1} {
			set startIndex -1
			set stopIndex -1
			set commandId ""
			set contentLength 0
			set receiveBuffer ""

			while {$commandId == ""} {
				::IxNet::CheckConnection

				if {[eof $::IxNet::_socketId]} {
					::IxNet::Close
					return
				}

				if {[catch {append receiveBuffer [read $::IxNet::_socketId 1]} errorMessage]} {
					::IxNet::Close
					if {[string first "connection reset by peer" $errorMessage] != -1} {
						error "connection reset by peer"
					} else {
						error $errorMessage
					}
				}

				set startIndex [string first $STARTINDEX $receiveBuffer]
				set stopIndex [string first $STOPINDEX $receiveBuffer]
				if {$startIndex != -1 && $stopIndex != -1} {
					set commandId [string range $receiveBuffer [expr $startIndex + 1] [expr $startIndex + 3]]

					if {[expr $startIndex + 4] < $stopIndex} {
						set contentLength [string range $receiveBuffer [expr $startIndex + 4] [expr $stopIndex - 1]]
					}
					break
				}
			}

			if {$_debugFlag} {
				puts "::IxNet::Read=$commandId $contentLength"; update
			}

			switch -- $commandId {
				"001" {
					set ::IxNet::_evalResult $TCL_ERROR
					set ::IxNet::_tclResult {}
					read $_socketId $contentLength
				}
				"003" {
					read $_socketId $contentLength
				}
				"004" {
					set _evalResult [read $_socketId $contentLength]
				}
				"007" {
					set filename [read $_socketId $contentLength]
				}
				"008" {
					if {[catch {file mkdir [file dirname $filename]} errorMessage]} {
						error "unable to create directory [file dirname $filename]"
					}
					if {[catch {set fid [open $filename w]} errorMessage]} {
						error "unable to create file $filename"
					}
					fconfigure $fid -translation binary
					fcopy $_socketId $fid -size $contentLength
					close $fid
				}
				"009" {
					set ::IxNet::_tclResult [read $_socketId $contentLength]
					return
				}
				default {
					error "unrecognized command $commandId"
				}
			}
		}
	}
	proc GetTclResult {} {
		variable _socketId
		variable _debugFlag
		variable _evalResult
		variable _tclResult

		::IxNet::Read

		if {$_debugFlag} {
			puts "::IxNet::GetTclResult= _evalResult=$_evalResult _tclResult=$_tclResult"; update
		} else {
			update
		}

		if {$_evalResult == 1} {
			error $_tclResult
		}

		if {!$::IxNet::_isClientTcl} {
			set ::IxNet::_parseResult $_tclResult
			::IxNet::ParseResult $_tclResult
			if {[string first "list" $::IxNet::_parseResult] == 0} {
				return [eval $::IxNet::_parseResult]
			} else {
				return $::IxNet::_parseResult
			}
		} else {
			return $_tclResult
		}
	}
	proc ParseResult {ixNetResult} {
		set firstList true
		set openReplacement "\[list"

		if {[string first "::ixNet::" $ixNetResult] == 0} {
			return
		}

		while {1} {
			set openBrace [string first "\{" $ixNetResult]
			if {$openBrace == -1} {
				break
			}

			# remove next additional side by side open brace and it's corresponding close brace
			while {[string index $ixNetResult [expr $openBrace + 1]] == "\{"} {
				set closeBrace [FindNextClosingBrace $ixNetResult $openBrace]
				if {$closeBrace != -1} {
					set ixNetResult [string replace $ixNetResult [expr $openBrace + 1] [expr $openBrace + 1]]
					incr closeBrace -1
					set ixNetResult [string replace $ixNetResult $closeBrace $closeBrace]
				} else {
					break
				}
			}

			set comma [string first "," $ixNetResult $openBrace]
			set datatype [string range $ixNetResult [expr $openBrace + 1] [expr $comma - 1]]
			set closeBrace [FindNextClosingBrace $ixNetResult $openBrace]

			set openReplacement ""
			set closeReplacement ""
			switch $datatype {
				"kArray" -
				"kStruct" {
					if {$firstList} {
						set openReplacement "list "
						set firstList false
					} else {
						set openReplacement "\[list "
						set closeReplacement "\]"
					}
				}
				default {
					if {!$firstList && [string first " " [string range $ixNetResult $openBrace $closeBrace]] != -1} {
						set openReplacement [binary format "c" 2]
						set closeReplacement [binary format "c" 3]
					}
				}
			}
			set ixNetResult [string replace $ixNetResult $openBrace $comma $openReplacement]
			set closeBrace [expr $closeBrace - (($comma - $openBrace) - [string length $openReplacement]) - 1]
			set ixNetResult [string replace $ixNetResult $closeBrace $closeBrace $closeReplacement]
		}
		set ::IxNet::_parseResult [string map [list [binary format "c" 2] "\{" [binary format "c" 3] "\}"] $ixNetResult]
	}
	proc FindNextClosingBrace {value {startPos 0}} {
		set depth 0

		for {set i $startPos} {$i < [string length $value]} {incr i} {
			if {[string index $value $i] == "\{"} {
				incr depth
			} elseif {[string index $value $i] == "\}"} {
				incr depth -1
				if {$depth == 0} {
					return $i
				}
			}
		}

		return -1
	}
	proc Buffer {command} {
		append ::IxNet::_buffer $command
		append ::IxNet::_buffer $::IxNet::BIN3

		return $::IxNet::_OK
	}
	proc SendBuffer {command} {
		append ::IxNet::_buffer $command
		append ::IxNet::_buffer $::IxNet::BIN3

		# send the buffer and then clear it
		if {[catch {set result [::IxNet::Send $::IxNet::_buffer]} errorMessage]} {
			unset ::IxNet::_buffer
			error $errorMessage
		}
		unset ::IxNet::_buffer

		return $result
	}
	proc PutFileOnServer {filename} {
		variable _socketId
		variable BIN2
		variable STX
		variable READFROM
		variable FILENAME
		variable CONTENTLENGTH
		variable CONTENT

		set fid [open $filename RDONLY]
		fconfigure $fid -buffering full -encoding binary -translation binary
		set truncatedFilename [file tail $filename]
		puts -nonewline $_socketId "<$STX><$READFROM><$FILENAME[string length $truncatedFilename]>$truncatedFilename<$CONTENT[file size $filename]>"
		fcopy $fid $_socketId
		flush $_socketId
		close $fid

		SetDefaultSocketModes

		set remoteFilename [IxNet::GetTclResult]

		return [IxNet::Send "ixNet${BIN2}readFrom${BIN2}${remoteFilename}${BIN2}-ixNetRelative"]
	}
	proc CreateFileOnServer {filename} {
		variable _socketId
		variable BIN2
		variable STX
		variable WRITETO
		variable FILENAME
		variable CONTENT

		puts -nonewline $_socketId "<$STX><$WRITETO><$FILENAME[string length $filename]>$filename<${CONTENT}0>"
		flush $_socketId

		set remoteFilename [::IxNet::GetTclResult]

		return [IxNet::Send "ixNet${BIN2}writeTo${BIN2}${remoteFilename}${BIN2}-ixNetRelative${BIN2}-overwrite"]
	}
	proc IsConnected {} {
		variable _socketId

		if {$_socketId == ""} {
			return false
		} else {
			return true
		}
	}
}

proc ::ixNet {args} {
	if {[llength $args] == 0} {
		error "Unknown command"
	}

	set command {}
	foreach {pattern} $::IxNet::commandPatterns {
		set patternIndex [lsearch -glob $args $pattern]
		if {$patternIndex != -1} {
			set command [lindex $args $patternIndex]
			break
		}
	}

	set ixNetCommand {}
	set first true
	foreach {arg} $args {
		if {$first} {
			set first false
			if {$arg != "ixNet"} {
				append ixNetCommand "ixNet[binary format "c" 2]"
			}
		} else {
			append ixNetCommand [binary format "c" 2]
		}

		if {[string length $arg] == 0} {
			append ixNetCommand "{}"
		} else {
			append ixNetCommand $arg
		}
	}

	switch -glob $command {
		"getRoot" {
			return {::ixNet::OBJ-/}
		}
		"getNull" {
			return {::ixNet::OBJ-null}
		}
		"connect" {
			set hostname [lindex $args 1]
			set port {8009}

			if {[llength $args] == 1} {
				error "ixNet connect <ipAddress> \[-port <8009>\] \[-version <5.30|5.40|5.50>\]"
			}

			array set argArray $args
			if {[info exists argArray(-port)]} {
				set port $argArray(-port)
			}

			if {[info exists ::tcl_platform(IXNETWORK_CLIENT_TYPE)]} {
				set ::IxNet::_isClientTcl false
				append ixNetCommand "${::IxNet::BIN2}-clientType${::IxNet::BIN2}${::tcl_platform(IXNETWORK_CLIENT_TYPE)}"
			}

			return [IxNet::Connect $hostname $port $ixNetCommand]
		}
		"disconnect" {
			if {[catch {IxNet::Disconnect $ixNetCommand} returnMessage]} {
				return "not connected"
			} else {
				return $returnMessage
			}
		}
		"commit" {
			return [IxNet::SendBuffer $ixNetCommand]
		}
		"readFrom" {
			# only bother with sending the file to the server if -ixNetRelative is not specified
			if {[lsearch -glob $args "-ixNetRelative"] == -1} {
				return [IxNet::PutFileOnServer [lindex $args 1]]
			} else {
				return [IxNet::SendBuffer $ixNetCommand]
			}
		}
		"writeTo" {
			# only bother with retrieving the file from the server if -ixNetRelative is not specified
			if {[lsearch -glob $args "-ixNetRelative"] == -1} {
				return [IxNet::CreateFileOnServer [lindex $args 1]]
			} else {
				return [IxNet::SendBuffer $ixNetCommand]
			}
		}
		"getVersion" {
			if {[IxNet::IsConnected]} {
				return [IxNet::SendBuffer $ixNetCommand]
			} else {
				return [package versions IxTclNetwork]
			}
		}
		"setSessionParameter" {
			if {[IxNet::IsConnected]} {
				return [IxNet::SendBuffer $ixNetCommand]
			} else {
				return [IxNet::Buffer $ixNetCommand]
			}
		}
		"setA*" -
		"setM*" {
			return [IxNet::Buffer $ixNetCommand]
		}
		default {
			return [IxNet::SendBuffer $ixNetCommand]
		}
	}

}
