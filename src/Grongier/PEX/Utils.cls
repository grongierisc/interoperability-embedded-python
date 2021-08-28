/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include Ensemble

Class Grongier.PEX.Utils
{

Parameter DOMAIN = "Ensemble";

ClassMethod RegisterComponent(pRemoteClassname As %String, pModule As %String, pCLASSPATHS As %String = "", pOverwrite As %Boolean = 0, pProxyClassname As %String = "") As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tLanguage,tExtraClasspaths,tDelimiter,tOnePath As %String = ""
	#dim tClassDetails,tRemoteSettings As %String = ""
	#dim tClasspaths As %ListOfDataTypes
	
	Quit:(""=pRemoteClassname) $$$ERROR($$$EnsErrGeneral,"Remote Classname must be specified in order to register a Production EXtensions component")
	Quit:(""=pModule) $$$ERROR($$$EnsErrGeneral,"Must specify the module of the remote code.")
		
	Try {

		set tClasspaths = ##class(%ListOfDataTypes).%New()
		set tDelimiter = $s($system.Version.GetOS()="Windows":";",1:":")
		set tExtraClasspaths = $tr(pCLASSPATHS,tDelimiter,"|")
		for i=1:1:$L(tExtraClasspaths,"|") {
			Set tOnePath = $P(tExtraClasspaths,"|",i)
			Continue:(""=tOnePath)
			Set:(tOnePath?1"$$IRISHOME"1P.E) tOnePath = $E($system.Util.InstallDirectory(),1,*-1)_$E(tOnePath,11,*)
			Do tClasspaths.Insert(tOnePath)
		}
		
		Set tSC = ..GetRemoteClassInfo(pRemoteClassname,pLanguageServer,tClasspaths,.tClassDetails,.tRemoteSettings)
		Quit:$$$ISERR(tSC)
		
		Set tConnectionSettings("CLASSPATHS") = pCLASSPATHS
		Set tConnectionSettings("ELS") = pLanguageServer
		Set tConnectionSettings("Language") = tLanguage
		Set tConnectionSettings("RemoteClassname") = pRemoteClassname
		Set:(""=pProxyClassname) pProxyClassname = pRemoteClassname
		
		Set tSC = ..GenerateProxyClass(pProxyClassname,.tConnectionSettings,tClassDetails,tRemoteSettings,pOverwrite)

	} Catch ex {
		Set tSC = ex.AsStatus()
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
		If $classmethod(pClassname,"%Extends","EnsLib.PEX.Common") {
			Set tClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname,,.tSC)
			Quit:$$$ISERR(tSC)
			If '$IsObject(tClass) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Proxy class for remote class '%1' could not be opened.",pClassname))
				Quit
			}
			Set tIsPEX = ("EnsLib.PEX.Utils" = tClass.GeneratedBy)
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

Query EnumeratePEXComponents(pSearchCriteria) As %Query(ROWSPEC = "Classname:%String,Type:%String,Language:%String,RemoteClass:%String") [ SqlProc ]
{
}

ClassMethod GetSearchCriteria(pSearchCriteria As %ZEN.proxyObject, ByRef qHandle) As %Status [ Internal ]
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	Set qHandle = ""
	
	Try {
		If $IsObject(pSearchCriteria) {
			
			Do pSearchCriteria.%CopyToArray(.tArray)
				
			#; Languages
			Set qHandle("Language","JAVA") = $G(tArray("Java"),0)
			Set qHandle("Language",".NET") = $G(tArray("DotNet"),0)
			Set qHandle("Language","PYTHON") = $G(tArray("Python"),0)
			Set qHandle("Language","Unspecified") = (qHandle("Language","JAVA") && qHandle("Language",".NET") && qHandle("Language","PYTHON"))
		
			#; Component Types
			Set qHandle("Type","Service") = $G(tArray("Service"),0)
			Set qHandle("Type","Process") = $G(tArray("Process"),0)
			Set qHandle("Type","Operation") = $G(tArray("Operation"),0)
			Set qHandle("Type","InboundAdapter") = $G(tArray("InboundAdapter"),0)
			Set qHandle("Type","OutboundAdapter") = $G(tArray("OutboundAdapter"),0)
			
		} Else {
			#; Languages
			Set qHandle("Language","JAVA") = 1
			Set qHandle("Language",".NET") = 1
			Set qHandle("Language","PYTHON") = 1
			Set qHandle("Language","Unspecified") = 1
			
			#; Component Types
			Set qHandle("Type","Service") = 1
			Set qHandle("Type","Process") = 1
			Set qHandle("Type","Operation") = 1
			Set qHandle("Type","InboundAdapter") = 1
			Set qHandle("Type","OutboundAdapter") = 1
		}
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

ClassMethod EnumeratePEXComponentsExecute(ByRef qHandle As %Binary, pSearchCriteria As %ZEN.proxyObject) As %Status [ Internal ]
{
	#dim tSC As %Status =$$$OK
	#dim tRS As %ResultSet = ##class(%ResultSet).%New("%Dictionary.ClassDefinitionQuery:SubclassOf")

	Do ..GetSearchCriteria(pSearchCriteria,.qHandle)
		
	If qHandle("Type","Service") {
		Set tSC = tRS.%Execute("EnsLib.PEX.BusinessService")
		Quit:$$$ISERR(tSC)
		While (tRS.Next(.tSC) && $$$ISOK(tSC)) {
			Set tClass = tRS.GetData(1)
			Set qHandle("Components",tClass) = $$$Text("Business Service")
		}
		Quit:$$$ISERR(tSC)
	}
	If qHandle("Type","Process") {
		Set tSC = tRS.%Execute("EnsLib.PEX.BusinessProcess")
		Quit:$$$ISERR(tSC)
		While (tRS.Next(.tSC) && $$$ISOK(tSC)) {
			Set tClass = tRS.GetData(1)
			Set qHandle("Components",tClass) = $$$Text("Business Process")
		}
		Quit:$$$ISERR(tSC)
	}
	If qHandle("Type","Operation") {
		Set tSC = tRS.%Execute("EnsLib.PEX.BusinessOperation")
		Quit:$$$ISERR(tSC)
		While (tRS.Next(.tSC) && $$$ISOK(tSC)) {
			Set tClass = tRS.GetData(1)
			Set qHandle("Components",tClass) = $$$Text("Business Operation")
		}
		Quit:$$$ISERR(tSC)
	}
	If qHandle("Type","InboundAdapter") {
		Set tSC = tRS.%Execute("EnsLib.PEX.InboundAdapter")
		Quit:$$$ISERR(tSC)
		While (tRS.Next(.tSC) && $$$ISOK(tSC)) {
			Set tClass = tRS.GetData(1)
			Set qHandle("Components",tClass) = $$$Text("Inbound Adapter")
		}
		Quit:$$$ISERR(tSC)
	}
	If qHandle("Type","OutboundAdapter") {
		Set tSC = tRS.%Execute("EnsLib.PEX.OutboundAdapter")
		Quit:$$$ISERR(tSC)
		While (tRS.Next(.tSC) && $$$ISOK(tSC)) {
			Set tClass = tRS.GetData(1)
			Set qHandle("Components",tClass) = $$$Text("Outbound Adapter")
		}
		Quit:$$$ISERR(tSC)
	}
	Quit tSC
}

ClassMethod EnumeratePEXComponentsFetch(ByRef qHandle As %Binary, ByRef Row As %List, ByRef AtEnd As %Integer = 0) As %Status [ Internal, PlaceAfter = EnumeratePEXComponentsExecute ]
{
	#dim tSC As %Status = $$$OK
	#dim tFoundOne As %Boolean = 0
	#dim tProp As %Dictionary.CompiledProperty
	#dim tKey,tLanguage,tType,tRemoteClass As %String = ""
	
	Set AtEnd = 0
	Set Row = ""
	Try {
		Do {
			Set qHandle=$O(qHandle("Components",qHandle),1,tType)
			If (""=qHandle) {
				Set Row="", AtEnd=1
				Quit
			}
			Set tClass = ##class(%Dictionary.CompiledClass).%OpenId(qHandle)
			If '$IsObject(tClass) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,"Class not found")
				Quit
			}
			
			Continue:("EnsLib.PEX.Utils" '= tClass.GeneratedBy)
			
			Set tLanguage = "Unspecified"
			For {
				Set tProp = tClass.Properties.GetNext(.tKey)	Quit:(""=tKey)
				If ("%remoteLanguage" = tProp.Name) {
					Set tLanguage = $$$StripQuotes(tProp.InitialExpression)
					Quit
				}
			}
			Continue:('qHandle("Language",tLanguage))

			Set tRemoteClass = $parameter(qHandle,"%REMOTECLASSNAME")
			
			Set Row=$LB(qHandle,tType,tLanguage,tRemoteClass)
			Set tFoundOne = 1

		} While 'tFoundOne
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

ClassMethod EnumeratePEXComponentsClose(ByRef qHandle As %Binary) As %Status [ Internal, PlaceAfter = EnumeratePEXComponentsFetch ]
{
	Kill qHandle
	Quit $$$OK
}

ClassMethod GetRemoteClassInfo(pRemoteClassname As %String, pLanguageServer As %String, pClasspaths As %String, ByRef pClassDetails, ByRef pRemoteSettings) As %Status [ Internal, Private ]
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tGateway As %External.Gateway
	#dim tGatewayProxy As %Net.Remote.Object
	
	Try {
		Set tGateway = $System.external.getGateway(pLanguageServer)
		Do tGateway.addToPath(pClasspaths)
		Set tGatewayProxy = tGateway.new(pRemoteClassname)
		
		If $IsObject(tGatewayProxy) {
			#; List of information about the class as a whole - $lb(SuperClass, Description, InfoURL, IconURL, Adapter)
			Set pClassDetails = tGatewayProxy."_getInfo"()
			#; List of information about the various properties of the class
			#; List of lists of form $lb(propName,dataType,defaultVal,required,category,description)
			Set pRemoteSettings = tGatewayProxy."_getProperties"()
		} Else {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Error opening gateway proxy for class '%1'"),pRemoteClassname)
		}
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

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
				If $classmethod(pClassname,"%Extends","EnsLib.PEX.Common") {
					#dim tClass As %Dictionary.CompiledClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname)
					If '$IsObject(tClass) {
						Set tSC = $$$ERROR($$$EnsErrGeneral,"Class not found")
						Quit
					}
					Set tIsPEX = ("EnsLib.PEX.Utils" = tClass.GeneratedBy)
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
		#dim tSuperClass As %String = $lg(pClassDetails,1)
		If (""=tSuperClass) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,"No PEX superclass found.")
			Quit
		}
		If '$Case($P(tSuperClass,".",1,*-1),"com.intersystems.enslib.pex":1,"iris.pex":1,"InterSystems.EnsLib.PEX.BusinessProcess":1,:0) ||
			'$Case($P(tSuperClass,".",*),"InboundAdapter":1,"OutboundAdapter":1,"BusinessService":1,"BusinessProcess":1,"BusinessOperation":1,:0) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,"Invalid superclass")
			Quit
		}
		Set tSuperClass = "EnsLib.PEX."_$P(tSuperClass,".",*)
		
		Set tCOSClass.Super = tSuperClass
		Set tCOSClass.GeneratedBy = $CLASSNAME()
		Set tCOSClass.ClassVersion = $$$CLASSDEFINITIONVERSION
		#dim tDescription As %String = $lg(pClassDetails,2)
		If (""'=tDescription) {
			Set tCOSClass.Description = $Replace(tDescription,$C(10),$C(13,10))
		}
		
		#; Do not display any of the connection settings
		#dim tSETTINGSParamValue As %String = "-%remoteClassname,-%remoteSettings,-%gatewayName,-%gatewayHost,-%gatewayPort,-%gatewayTimeout,-%gatewayExtraClasspaths"
		If (tSuperClass [ "Adapter") {
			Set tSETTINGSParamValue = tSETTINGSParamValue_",-%useHostConnection"
		}
		
		#dim tParamClassname As %Dictionary.ParameterDefinition = ##class(%Dictionary.ParameterDefinition).%New()
		Set tParamClassname.Name = "%REMOTECLASSNAME"
		Set tParamClassname.Default = pConnectionSettings("RemoteClassname")
		Set tSC = tCOSClass.Parameters.Insert(tParamClassname)
		Quit:$$$ISERR(tSC)
		
		#dim tPropClassname As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropClassname.Name = "%remoteClassname"
		Set tPropClassname.Type = "%String"
		Set tPropClassname.ReadOnly = 1
		Set tPropClassname.Internal = 1
		Set tSC = tCOSClass.Properties.Insert(tPropClassname)
		Quit:$$$ISERR(tSC)
		
		#dim tClassnameMethod As %Dictionary.MethodDefinition = ##class(%Dictionary.MethodDefinition).%New()
		Set tClassnameMethod.Name = "%remoteClassnameGet"
		Set tSC = tClassnameMethod.Implementation.WriteLine($C(9)_"quit ..#%REMOTECLASSNAME")	Quit:$$$ISERR(tSC)
		Set tSC = tCOSClass.Methods.Insert(tClassnameMethod)
		Quit:$$$ISERR(tSC)

		#dim tURL As %String = $lg(pClassDetails,3)
		If ""'=tURL {
			#dim tParamURL As %Dictionary.ParameterDefinition = ##class(%Dictionary.ParameterDefinition).%New()
			Set tParamURL.Name = "%URL"
			Set tParamURL.Default = tURL
			Set tSC = tCOSClass.Parameters.Insert(tParamURL)
			Quit:$$$ISERR(tSC)
		}
		
		#dim tPropClasspaths As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropClasspaths.Name = "%gatewayExtraClasspaths"
		Set tPropClasspaths.Type = "%String"
		Set tSC = tPropClasspaths.Parameters.SetAt("","MAXLEN")
		Quit:$$$ISERR(tSC)
		Set tPropClasspaths.InitialExpression = $$$quote(pConnectionSettings("CLASSPATHS"))
		Set tPropClasspaths.Description = $$$Text("One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Remote Gateway")
		Set tSC = tCOSClass.Properties.Insert(tPropClasspaths)
		Quit:$$$ISERR(tSC)
		
		#dim tPropELS As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropELS.Name = "%gatewayName"
		Set tPropELS.Type = "%String"
		Set tPropELS.Description = $$$Text("External Language Server Name")
		Set tPropELS.InitialExpression = $$$quote(pConnectionSettings("ELS"))
		Set tPropELS.Internal = 1
		Set tSC = tCOSClass.Properties.Insert(tPropELS)
		Quit:$$$ISERR(tSC)
		
		#dim tPropLanguage As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
		Set tPropLanguage.Name = "%remoteLanguage"
		Set tPropLanguage.Type = "%String"
		Set tPropLanguage.Internal = 1
		Set tPropLanguage.InitialExpression = $$$quote($zcvt(pConnectionSettings("Language"),"U"))
		Set tSC = tCOSClass.Properties.Insert(tPropLanguage)
		Quit:$$$ISERR(tSC)
		
		#dim tMethod As %Dictionary.MethodDefinition = ##class(%Dictionary.MethodDefinition).%New()
		Set tMethod.Name = "SetPropertyValues"
		
		#dim tCustomProp As %Dictionary.PropertyDefinition
		#dim tPropInfo,tPropName,tDataType,tDefault,tDesc,tPropCat,tContext As %String
		#; each remote setting is of form $lb(propName,dataType,defaultVal,required,category,description,editorContext)
		For i=1:1:$ll(pRemoteSettings) {
			Set tPropInfo = $lg(pRemoteSettings,i)
			Continue:""=tPropInfo ; this shouldn't happen, but just in case
			Set tPropName = $lg(tPropInfo,1)
			Set tDataType = $lg(tPropInfo,2)
			If (""=tPropName) || (""=tDataType) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,"All properties must have a name and datatype defined")
				Quit
			}
			Set tCustomProp = ##class(%Dictionary.PropertyDefinition).%New()
			Set tCustomProp.Name = tPropName
			If $Case(tDataType,"String":1,"Integer":1,"Boolean":1,"Numeric":1,:0) {
				Set tDataType = "%"_tDataType
			} ElseIf '##class(%Dictionary.ClassDefinition).%ExistsId(tDataType) {
				Set tDataType = "%String"
			}
			Set tCustomProp.Type = tDataType
			Set tDefault = $lg(tPropInfo,3)
			If ""'=tDefault {
				Set tCustomProp.InitialExpression = $$$quote(tDefault)
			}
			Set tCustomProp.Required = $lg(tPropInfo,4,0)
			Set tDesc = $lg(tPropInfo,6)
			If ""'=tDesc {
				Set tDesc = $zstrip($Replace(tDesc,$C(10),$C(13,10)),"<>W")
				Set:$E(tDesc,*-1,*)=$C(13,10) tDesc = $E(tDesc,1,*-2)
				Set tCustomProp.Description = tDesc
			}
			
			Set tSC = tCOSClass.Properties.Insert(tCustomProp)
			Quit:$$$ISERR(tSC)
			
			Set tPropCat = $lg(tPropInfo,5,"Additional")
			Set tSETTINGSParamValue = tSETTINGSParamValue_","_tPropName_":"_tPropCat
			
			Set tSC = tMethod.Implementation.WriteLine($char(9)_"try {")	Quit:$$$ISERR(tSC)
			Set tSC = tMethod.Implementation.WriteLine($char(9,9)_"set $property(..%gatewayProxy,"_$$$quote(tPropName)_") = .."_tPropName)	Quit:$$$ISERR(tSC)
			Set tSC = tMethod.Implementation.WriteLine($char(9)_"} catch ex {")	Quit:$$$ISERR(tSC)
			Set tSC = tMethod.Implementation.WriteLine($char(9,9)_"$$$LOGWARNING(ex.DisplayString())")	Quit:$$$ISERR(tSC)
			Set tSC = tMethod.Implementation.WriteLine($char(9)_"}")	Quit:$$$ISERR(tSC)
		}
		Quit:$$$ISERR(tSC)
		#; Avoid possiblity of empty method if no properties to set
		Set tSC = tMethod.Implementation.WriteLine($char(9)_"quit")	Quit:$$$ISERR(tSC)
		
		If $Case(tSuperClass,"EnsLib.PEX.BusinessService":1,"EnsLib.PEX.BusinessOperation":1,:0) {
			Set tSETTINGSParamValue = tSETTINGSParamValue_",-%useAdapterConnection"
			#dim tAdapterClass = $lg(pClassDetails,5)
			If (""'=tAdapterClass) {
				#; May want to issue a warning in the UI if the Adapter class does not exist
				#; but we don't check here because it does compile and may just be that the user is registering the Service/Operation before the Adapter
				#dim tADAPTERParam As %Dictionary.ParameterDefinition = ##class(%Dictionary.ParameterDefinition).%New()
				Set tADAPTERParam.Name = "ADAPTER"
				Set tADAPTERParam.Default = tAdapterClass
				Set tSC = tCOSClass.Parameters.Insert(tADAPTERParam)
				Quit:$$$ISERR(tSC)
				#; If remote Business Service or Operation specified an Adapter and said to use the Adapter connection, set %useAdapterConnection
				If (1 = $lg(pClassDetails,6)) {
					#dim tAdapterConnProp As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
					Set tAdapterConnProp.Name = "%useAdapterConnection"
					Set tAdapterConnProp.Type = "%Boolean"
					Set tAdapterConnProp.Internal = 1
					Set tAdapterConnProp.InitialExpression = 1
					Set tAdapterConnProp.Description = $$$Text("Use Adapter Connection. If set to true, this business host will use the connection from the adapter.")
					Set tSC = tCOSClass.Properties.Insert(tAdapterConnProp)
					Quit:$$$ISERR(tSC)
				}
			}
		}
		
		#dim tSETTINGSParam As %Dictionary.ParameterDefinition = ##class(%Dictionary.ParameterDefinition).%New()
		Set tSETTINGSParam.Name = "SETTINGS"
		Set tSETTINGSParam.Default = tSETTINGSParamValue
		Set tSC = tCOSClass.Parameters.Insert(tSETTINGSParam)
		Quit:$$$ISERR(tSC)
		
		Set tSC = tCOSClass.Methods.Insert(tMethod)
		Quit:$$$ISERR(tSC)
		
		Set tSC = tCOSClass.%Save()
		Quit:$$$ISERR(tSC)
		
		Set tSC = $System.OBJ.Compile(pClassname,"-d")
		
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

ClassMethod Count() As %Integer [ Internal ]
{
	#dim tCount As %Integer = 0
	&sql(SELECT COUNT(*) INTO :tCount FROM %Dictionary.CompiledClass Where GeneratedBy = 'EnsLib.PEX.Utils')
	Quit tCount
}

ClassMethod GetComponentProxy(pClassname As %String, Output pProxy As %ZEN.proxyObject) As %Status [ Internal ]
{
	#dim tSC = $$$OK
	#dim tAdapter,tPropName,tClasspaths,tDelimiter As %String = ""
	#dim tClass As %Dictionary.CompiledClass
	#dim tProp As %Dictionary.PropertyDefinition
	#dim tSettingsCreated As %Boolean = 0
	#dim tClasspathList,tProxySettingsList As %Library.ListOfObjects
	#dim tProxySetting As %ZEN.proxyObject
	
	If ##class(%Dictionary.CompiledClass).%ExistsId(pClassname) {
		Set pProxy = ##class(%ZEN.proxyObject).%New()
		Set tClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname)
		
		Set pProxy.Name = pClassname
		Set pProxy.Description = tClass.Description
		Set pProxy.LastUpdated = $zdatetime(tClass.TimeCreated)
		
		#; Check for ADAPTER, URL, and REMOTECLASSNAME
		If $Case(tClass.Super,"EnsLib.PEX.BusinessService":1,"EnsLib.PEX.BusinessOperation":1,:0) {
			Set tAdapter = $parameter(pClassname,"ADAPTER")
			Set pProxy.Adapter = $S(""'=tAdapter:tAdapter,1:$$$Text("None"))
			Set pProxy.UseAdapterConnection = $$$Text("False") ; default to false
		}
		Set pProxy.URL = $parameter(pClassname,"%URL")
		Set pProxy.RemoteClassname = $parameter(pClassname,"%REMOTECLASSNAME")
		
		For i=1:1:tClass.Properties.Count() {
			Set tProp = tClass.Properties.GetAt(i)
			Set tPropName = tProp.Name
			Continue:$Case(tPropName,"%remoteClassname":1,"%remoteLanguage":1,:0)
			
			If ("%gatewayExtraClasspaths" = tPropName) {
				Set tClasspathList = ##class(%Library.ListOfDataTypes).%New()
				Set tClasspaths = $$$StripQuotes(tProp.InitialExpression)
				set tDelimiter = $s($system.Version.GetOS()="Windows":";",1:":")
				set tClasspaths = $tr(tClasspaths,tDelimiter,"|")
				for j=1:1:$L(tClasspaths,"|") {
					Set tOnePath = $P(tClasspaths,"|",j)
					Continue:(""=tOnePath)
					Set tSC= tClasspathList.Insert(tOnePath)	Quit:$$$ISERR(tSC)
				}
				Set pProxy.Classpaths = tClasspathList
			} ElseIf ("%gatewayName" = tPropName) {
				Set pProxy.LanguageServer = $$$StripQuotes(tProp.InitialExpression)
			} ElseIf ("%useAdapterConnection" = tPropName) {
				Set pProxy.UseAdapterConnection = $Select(tProp.InitialExpression:$$$Text("True"),1:$$$Text("False"))
			} ElseIf (pClassname=tProp.Origin) {
				If 'tSettingsCreated {
					Set tProxySettingsList = ##class(%Library.ListOfObjects).%New()
					Set tSettingsCreated = 1
				}
				Set tProxySetting = ##class(%ZEN.proxyObject).%New()
				Set tProxySetting.LocalizedName = $$FormatMessage^%occMessages($$$SessionLanguage,"EnsColumns",tPropName,tPropName)
				Set tProxySetting.Name = tPropName
				Set tProxySetting.Default = $S(+tProp.InitialExpression = tProp.InitialExpression: +tProp.InitialExpression,1:$$$StripQuotes(tProp.InitialExpression))
				Set tProxySetting.Description = tProp.Description
				Set tProxySetting.Type = $S("%Library."=$E(tProp.Type,1,9):"%"_$E(tProp.Type,10,*),1:tProp.Type)
				Set tProxySetting.Required = tProp.Required
				Set tSC = tProxySettingsList.Insert(tProxySetting)	Quit:$$$ISERR(tSC)
			}
		}
		
		If tSettingsCreated {
			Set pProxy.Settings = tProxySettingsList
		}
		
	} Else {
		Set pProxy = $$$NULLOREF
	}
	Quit tSC
}

}
