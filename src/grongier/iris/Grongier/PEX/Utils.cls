/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include Ensemble

Class Grongier.PEX.Utils [ Abstract ]
{

ClassMethod dispatchRegisterComponent(pModule As %String, pRemoteClassname As %String, pCLASSPATHS As %String = "", pOverwrite As %Boolean = 0, pProxyClassname As %String = "") As %Status
{
	set tSc = $$$OK
	$$$ThrowOnError(##class(Grongier.PEX.Utils).RegisterComponent(pModule, pRemoteClassname, pCLASSPATHS, pOverwrite , pProxyClassname))
	return tSc
}

/// "bo","Duplex","/irisdev/app/src/python/demo/duplex/",1,"Duplex.Duplex"
ClassMethod RegisterComponent(pModule As %String, pRemoteClassname As %String, pCLASSPATHS As %String = "", pOverwrite As %Boolean = 0, pProxyClassname As %String = "") As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tLanguage,tExtraClasspaths,tDelimiter,tOnePath As %String = ""
	#dim tClassDetails,tRemoteSettings As %String = ""
	#dim tClasspaths As %ListOfDataTypes
	
	Quit:(""=pRemoteClassname) $$$ERROR($$$EnsErrGeneral,"Remote Classname must be specified in order to register a Production EXtensions component")
	Quit:(""=pModule) $$$ERROR($$$EnsErrGeneral,"Must specify the module of the remote code.")
		
	Try {

		$$$ThrowOnError(..GetRemoteClassInfo(pRemoteClassname,pModule,pCLASSPATHS,.tClassDetails,.tRemoteSettings))

		Set tConnectionSettings("Classpaths") = pCLASSPATHS
		Set tConnectionSettings("Module") = pModule
		Set tConnectionSettings("Classname") = pRemoteClassname
		Set:(""=pProxyClassname) pProxyClassname = "User."_pRemoteClassname
		
		$$$ThrowOnError(..GenerateProxyClass(pProxyClassname,.tConnectionSettings,tClassDetails,tRemoteSettings,pOverwrite))

	} Catch ex {
		set msg = $System.Status.GetOneStatusText(ex.AsStatus(),1)
		set tSC = $$$ERROR($$$EnsErrGeneral,msg)
	}

	Quit tSC
}

ClassMethod DeleteComponentProxy(pClassname As %String = "") As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tIsPEX As %Boolean = 0
	#dim tClass As %Dictionary.CompiledClass
	
	Quit:(""=pClassname) $$$ERROR($$$EnsErrGeneral,"Remote class name must be specified.")
	
	Try {
		
		If '##class(%Dictionary.ClassDefinition).%ExistsId(pClassname) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("No proxy class defined for remote class '%1'.",pClassname))
			Quit
		}
		If $classmethod(pClassname,"%Extends","Grongier.PEX.Common") {
			Set tClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname,,.tSC)
			Quit:$$$ISERR(tSC)
			If '$IsObject(tClass) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Proxy class for remote class '%1' could not be opened.",pClassname))
				Quit
			}
			Set tIsPEX = ("Grongier.PEX.Utils" = tClass.GeneratedBy)
		}
		If tIsPEX {
			Set tSC = ##class(%Dictionary.ClassDefinition).%DeleteId(pClassname)
			If $$$ISERR(tSC) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Unable to delete proxy class for remote class '%1' : '%2'.",pClassname,$System.Status.GetErrorText(tSC)))
				Quit
			}
		} Else {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Cannot delete class '%1' because it is not a PEX proxy class.",pClassname))
			Quit
		}
		
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

// ..GetRemoteClassInfo(pRemoteClassname,pModule,pCLASSPATHS,.tClassDetails,.tRemoteSettings)

ClassMethod GetRemoteClassInfo(pRemoteClassname As %String, pModule As %String, pClasspaths As %String, ByRef pClassDetails, ByRef pRemoteSettings) As %Status [ Internal, Private ]
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tGateway As %External.Gateway
	#dim tGatewayProxy As %Net.Remote.Object
	
	Try {
		if pClasspaths '="" {
			set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
			set extraClasspaths = $tr(pClasspaths,delimiter,"|")
			for i=1:1:$l(extraClasspaths,"|") {
				set onePath = $p(extraClasspaths,"|",i)
				set onePath = ##class(%File).NormalizeDirectory(onePath)
				if onePath?1"$$IRISHOME"1P.E set onePath = $e($system.Util.InstallDirectory(),1,*-1)_$e(onePath,11,*)
				if onePath'="" do ##class(Grongier.PEX.Python).SetClassPath(onePath)
			}
		}
		;

		set tClass = ##class(Grongier.PEX.Python).GetInstanceFromModuleClassName(pModule,pRemoteClassname)

		If $IsObject(tClass) {
			#; List of information about the class as a whole - $lb(SuperClass, Description, InfoURL, IconURL, Adapter)
			Set pClassDetails = tClass."_get_info"()
			#; List of information about the various properties of the class
			#; List of lists of form $lb(propName,dataType,defaultVal,required,category,description)
			Set pRemoteSettings = tClass."_get_properties"()
		} Else {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Error opening gateway proxy for class '%1'"),pRemoteClassname)
		}
	} Catch ex {
		set msg = $System.Status.GetOneStatusText(ex.AsStatus(),1)
		set tSC = $$$ERROR($$$EnsErrGeneral,msg)
	}
	
	Quit tSC
}

/// Set tConnectionSettings("Classpaths") = pCLASSPATHS
/// Set tConnectionSettings("Module") = pModule
/// Set tConnectionSettings("Classname") = pRemoteClassname
/// Set:(""=pProxyClassname) pProxyClassname = pRemoteClassname
/// 
/// Set tSC = ..GenerateProxyClass(pProxyClassname,.tConnectionSettings,tClassDetails,tRemoteSettings,pOverwrite)
/// "bo","Duplex","/irisdev/app/src/python/demo/duplex/",1,"Duplex.Duplex"
ClassMethod GenerateProxyClass(pClassname As %String, ByRef pConnectionSettings, pClassDetails As %String = "", pRemoteSettings As %String = "", pOverwrite As %Boolean = 0) As %Status [ Internal, Private ]
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	
	Quit:(""=pClassname) $$$ERROR($$$EnsErrGeneral,"Class name must be specified in order to generate a proxy class for this Production EXtensions component")
	
	Try {

		If ##class(%Dictionary.ClassDefinition).%ExistsId(pClassname) {
			If 'pOverwrite {
				Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Proxy class '%1' already exists.",pClassname))
				Quit
			} Else {
				#dim tIsPEX As %Boolean = 0
				If $classmethod(pClassname,"%Extends","Grongier.PEX.Common") {
					#dim tClass As %Dictionary.CompiledClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname)
					If '$IsObject(tClass) {
						Set tSC = $$$ERROR($$$EnsErrGeneral,"Class not found")
						Quit
					}
					Set tIsPEX = ("Grongier.PEX.Utils" = tClass.GeneratedBy)
				}
				If tIsPEX {
					Set tSC = ##class(%Dictionary.ClassDefinition).%DeleteId(pClassname)
					If $$$ISERR(tSC) {
						Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Unable to delete existing proxy class '%1' : '%2'.",pClassname,$System.Status.GetErrorText(tSC)))
						Quit
					}
				} Else {
					Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Cannot overwrite class '%1' because it is not a PEX proxy class.",pClassname))
					Quit
				}
			}
		}
		
		#; create subclass of the ObjectScript Business Host
		#dim tCOSClass As %Dictionary.ClassDefinition
		Set tCOSClass = ##class(%Dictionary.ClassDefinition).%New()
		Set tCOSClass.Name = pClassname

		#dim tSuperClass As %String = pClassDetails."__getitem__"(0)
		If (""=tSuperClass) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,"No PEX superclass found.")
			Quit
		}
		If '$Case($P(tSuperClass,".",*),"DuplexProcess":1,"DuplexService":1,"DuplexOperation":1,"InboundAdapter":1,"OutboundAdapter":1,"BusinessService":1,"BusinessProcess":1,"BusinessOperation":1,:0) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,"Invalid superclass")
			Quit
		}
		Set tSuperClass = "Grongier.PEX."_$P(tSuperClass,".",*)
		
		Set tCOSClass.Super = tSuperClass
		Set tCOSClass.GeneratedBy = $CLASSNAME()
		Set tCOSClass.ClassVersion = $$$CLASSDEFINITIONVERSION
		#dim tDescription As %String = pClassDetails."__getitem__"(1)
		If (""'=tDescription) {
			Set tCOSClass.Description = $Replace(tDescription,$C(10),$C(13,10))
		}
		
		#; Do not display any of the connection settings
		#dim tSETTINGSParamValue As %String = "%classname:Python $type,%module:Python $type,%settings:Python $type,%classpaths:Python $type"
		
		#dim tPropClassname As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropClassname.Name = "%classname"
		Set tPropClassname.Type = "%String"
		Set tPropClassname.InitialExpression = $$$quote(pConnectionSettings("Classname"))
		Set tPropClassname.Internal = 1
		Set tSC = tCOSClass.Properties.Insert(tPropClassname)
		Quit:$$$ISERR(tSC)
		
		
		#dim tPropClasspaths As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropClasspaths.Name = "%classpaths"
		Set tPropClasspaths.Type = "%String"
		Set tSC = tPropClasspaths.Parameters.SetAt("","MAXLEN")
		Quit:$$$ISERR(tSC)
		Set tPropClasspaths.InitialExpression = $$$quote(pConnectionSettings("Classpaths"))
		Set tPropClasspaths.Description = "One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Remote Gateway"
		Set tSC = tCOSClass.Properties.Insert(tPropClasspaths)
		Quit:$$$ISERR(tSC)
		
		
		#dim tPropLanguage As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropLanguage.Name = "%module"
		Set tPropLanguage.Type = "%String"
		Set tPropLanguage.Internal = 1
		Set tPropLanguage.InitialExpression = $$$quote(pConnectionSettings("Module"))
		Set tSC = tCOSClass.Properties.Insert(tPropLanguage)
		Quit:$$$ISERR(tSC)
		
		If $Case(tSuperClass,"Grongier.PEX.BusinessService":1,"Grongier.PEX.BusinessOperation":1,"Grongier.PEX.DuplexService":1,"Grongier.PEX.DuplexOperation":1,:0) {
			
			If (##class(Grongier.PEX.Python).Len(pClassDetails)>4) { //Adaptor

				#dim tAdapterClass = pClassDetails."__getitem__"(4)
				#; May want to issue a warning in the UI if the Adapter class does not exist
				#; but we don't check here because it does compile and may just be that the user is registering the Service/Operation before the Adapter
				#dim tADAPTERParam As %Dictionary.ParameterDefinition = ##class(%Dictionary.ParameterDefinition).%New()
				Set tADAPTERParam.Name = "ADAPTER"
				Set tADAPTERParam.Default = tAdapterClass
				Set tSC = tCOSClass.Parameters.Insert(tADAPTERParam)
				Quit:$$$ISERR(tSC)
			}
		}

		set type = ""
		set:($Case(tSuperClass,"Grongier.PEX.InboundAdapter":1,"Grongier.PEX.OutboundAdapter":1,:0)) type = "Adapter"
		set tSETTINGSParamValue = $REPLACE(tSETTINGSParamValue,"$type",type)
		
		#dim tSETTINGSParam As %Dictionary.ParameterDefinition = ##class(%Dictionary.ParameterDefinition).%New()
		Set tSETTINGSParam.Name = "SETTINGS"
		Set tSETTINGSParam.Default = tSETTINGSParamValue
		Set tSC = tCOSClass.Parameters.Insert(tSETTINGSParam)
		Quit:$$$ISERR(tSC)
		
		Set tSC = tCOSClass.%Save()
		Quit:$$$ISERR(tSC)
		
		Set tSC = $System.OBJ.Compile(pClassname,"-d")
		
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

// Thanks to Alex Woodhead for this serializer
ClassMethod ListFrompyList(ByRef pyList As %SYS.Python = {$$$NULLOREF}, ByRef impBi As %SYS.Python = {##class(%SYS.Python).Import("builtins")}, msgkeys = "") As %SYS.Python [ ProcedureBlock = 1 ]
{
	set ret=$LB()
	// How to get length of list
	set listlen=impBi.len(pyList)
	for i=1:1:listlen {
		set data=..pyListGet(i,pyList)
		// if data is also a list // TODO
		if $IsObject(data) {
			if ..pyListIs(data) {
			  set data=..ListFrompyList(data,impBi,,msgkeys_"["_i_"]")
			} else {
				set $ZE="Class "_..%ClassName(1)_" Method ListFrompyList. Unsupported value type """_..pyTypeName(data)_""" at position "_msgkeys_"["_i_"]"
				do BACK^%ETN	
			}
		}
		// add string / numeric / IRIS LIST to ret
		set ret=$LU(ret,i,data)
	}
	quit ret
}

ClassMethod pyListIs(ByRef pyList As %SYS.Python) As %SYS.Python [ Language = python ]
{
	return (type(pyList)==list)
}

/// Returns empty string on error
/// position starts at one to keep same as IRIS List
ClassMethod pyListGet(position As %Integer, ByRef pyList As %SYS.Python) As %SYS.Python [ Language = python ]
{
	ret=""
	try:
	  ret=(pyList[position-1])
	except:
	  print("Error in pyListGet")
	  
	return ret
}

ClassMethod pyTypeName(obj As %SYS.Python) As %String [ Language = python ]
{
	return type(obj).__name__
}

}
