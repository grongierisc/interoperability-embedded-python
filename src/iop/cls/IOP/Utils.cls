/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include Ensemble

Class IOP.Utils Extends %RegisteredObject
{

ClassMethod dispatchRegisterComponent(
	pModule As %String,
	pRemoteClassname As %String,
	pCLASSPATHS As %String = "",
	pFullpath As %String = "",
	pOverwrite As %Boolean = 0,
	pProxyClassname As %String = "") As %Status
{
	set tSc = $$$OK
	$$$ThrowOnError(##class(IOP.Utils).RegisterComponent(pModule, pRemoteClassname, pCLASSPATHS, pFullpath, pOverwrite , pProxyClassname))
	return tSc
}

/// "bo","Duplex","/irisdev/app/src/python/demo/duplex/",1,"Duplex.Duplex"
ClassMethod RegisterComponent(
	pModule As %String,
	pRemoteClassname As %String,
	pCLASSPATHS As %String = "",
	pFullpath As %String = "",
	pOverwrite As %Boolean = 0,
	pProxyClassname As %String = "") As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tLanguage,tExtraClasspaths,tDelimiter,tOnePath As %String = ""
	#dim tClassDetails,tRemoteSettings As %String = ""
	#dim tClasspaths As %ListOfDataTypes
	
	Quit:(""=pRemoteClassname) $$$ERROR($$$EnsErrGeneral,"Remote Classname must be specified in order to register a Production EXtensions component")
	Quit:(""=pModule) $$$ERROR($$$EnsErrGeneral,"Must specify the module of the remote code.")
		
	Try {

		$$$ThrowOnError(..GetRemoteClassInfo(pRemoteClassname,pModule,pCLASSPATHS,pFullpath,.tClassDetails,.tRemoteSettings))

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
	#dim tIsIOP As %Boolean = 0
	#dim tClass As %Dictionary.CompiledClass
	
	Quit:(""=pClassname) $$$ERROR($$$EnsErrGeneral,"Remote class name must be specified.")
	
	Try {
		
		If '##class(%Dictionary.ClassDefinition).%ExistsId(pClassname) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("No proxy class defined for remote class '%1'.",pClassname))
			Quit
		}
		If $classmethod(pClassname,"%Extends","IOP.Common") {
			Set tClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname,,.tSC)
			Quit:$$$ISERR(tSC)
			If '$IsObject(tClass) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Proxy class for remote class '%1' could not be opened.",pClassname))
				Quit
			}
			Set tIsIOP = ("IOP.Utils" = tClass.GeneratedBy)
		}
		If tIsIOP {
			Set tSC = ##class(%Dictionary.ClassDefinition).%DeleteId(pClassname)
			If $$$ISERR(tSC) {
				Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Unable to delete proxy class for remote class '%1' : '%2'.",pClassname,$System.Status.GetErrorText(tSC)))
				Quit
			}
		} Else {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Cannot delete class '%1' because it is not a IOP proxy class.",pClassname))
			Quit
		}
		
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

// ..GetRemoteClassInfo(pRemoteClassname,pModule,pCLASSPATHS,.tClassDetails,.tRemoteSettings)

ClassMethod GetRemoteClassInfo(
	pRemoteClassname As %String,
	pModule As %String,
	pClasspaths As %String,
	pFullpath As %String = "",
	ByRef pClassDetails,
	ByRef pRemoteSettings) As %Status [ Internal ]
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	
	Try {
		if pClasspaths '="" {
			set sys = ##class(%SYS.Python).Import("sys")
			set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
			set extraClasspaths = $tr(pClasspaths,delimiter,"|")
			for i=1:1:$l(extraClasspaths,"|") {
				set onePath = $p(extraClasspaths,"|",i)
				set onePath = ##class(%File).NormalizeDirectory(onePath)
				if onePath?1"$$IRISHOME"1P.E set onePath = $e($system.Util.InstallDirectory(),1,*-1)_$e(onePath,11,*)
				if onePath'="" do ##class(IOP.Common).SetPythonPath(onePath)
			}
		}

		set importlib = ##class(%SYS.Python).Import("importlib")
		set builtins = ##class(%SYS.Python).Import("builtins")
		// Load the module form a specific path
		Try {
			set spec = importlib.util."spec_from_file_location"(pModule, pFullpath)
			set module = importlib.util."module_from_spec"(spec)
			do sys.modules."__setitem__"(pModule, module)
			do spec.loader."exec_module"(module)
		}
		Catch ex {
			// If the module is not found, try to import the frist one found
			set module = importlib."import_module"(pModule)
		}

		// Get the class
		set class = builtins.getattr(module, pRemoteClassname)
		set tClass = class."__new__"(class)

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

ClassMethod GenerateProxyClass(
	pClassname As %String,
	ByRef pConnectionSettings,
	pClassDetails As %String = "",
	pRemoteSettings As %String = "",
	pOverwrite As %Boolean = 0) As %Status [ Internal, Private ]
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
				#dim tIsIOP As %Boolean = 0
				If $classmethod(pClassname,"%Extends","IOP.Common") {
					#dim tClass As %Dictionary.CompiledClass = ##class(%Dictionary.CompiledClass).%OpenId(pClassname)
					If '$IsObject(tClass) {
						Set tSC = $$$ERROR($$$EnsErrGeneral,"Class not found")
						Quit
					}
					Set tIsIOP = ("IOP.Utils" = tClass.GeneratedBy)
				}
				If tIsIOP {
					Set tSC = ##class(%Dictionary.ClassDefinition).%DeleteId(pClassname)
					If $$$ISERR(tSC) {
						Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Unable to delete existing proxy class '%1' : '%2'.",pClassname,$System.Status.GetErrorText(tSC)))
						Quit
					}
				} Else {
					Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Cannot overwrite class '%1' because it is not a IOP proxy class.",pClassname))
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
			Set tSC = $$$ERROR($$$EnsErrGeneral,"No IOP superclass found.")
			Quit
		}
		If '$Case($P(tSuperClass,".",*),"DuplexProcess":1,"DuplexService":1,"DuplexOperation":1,"InboundAdapter":1,"OutboundAdapter":1,"BusinessService":1,"BusinessProcess":1,"BusinessOperation":1,:0) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,"Invalid superclass")
			Quit
		}
		Set tSuperClass = "IOP."_$P(tSuperClass,".",*)
		
		Set tCOSClass.Super = tSuperClass
		Set tCOSClass.GeneratedBy = $CLASSNAME()
		Set tCOSClass.ClassVersion = $$$CLASSDEFINITIONVERSION
		#dim tDescription As %String = pClassDetails."__getitem__"(1)
		If (""'=tDescription) {
			Set tCOSClass.Description = $Replace(tDescription,$C(10),$C(13,10))
		}
		
		#; Do not display any of the connection settings
		#dim tSETTINGSParamValue As %String = "%classname:Python $type,%module:Python $type,%settings:Python $type,%classpaths:Python $type,%enable:Python Debug $type,%timeout:Python Debug $type,%port:Python Debug $type,%PythonInterpreterPath:Python Debug $type,%traceback:Python Debug $type"
		
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
		
		If $Case(tSuperClass,"IOP.BusinessService":1,"IOP.BusinessOperation":1,"IOP.DuplexService":1,"IOP.DuplexOperation":1,:0) {
			set builtins = ##class(%SYS.Python).Import("builtins")
			If (builtins.len(pClassDetails)>4) { //Adaptor

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
		
		#dim tCustomProp As %Dictionary.PropertyDefinition
		#dim tPropInfo,tPropName,tDataType,tDefault,tDesc,tPropCat,tContext As %String

		set builtins = ##class(%SYS.Python).Import("builtins")
		#; each remote setting is of form $lb(propName,dataType,defaultVal,required,category,description,editorContext)
		For i=0:1:builtins.len(pRemoteSettings)-1 {
			Set tPropInfo = pRemoteSettings."__getitem__"(i)
			Continue:""=tPropInfo ; this shouldn't happen, but just in case
			Set tPropName = tPropInfo."__getitem__"(0)
			Set tDataType = tPropInfo."__getitem__"(1)
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
			If tDataType["%String" {
				Set tSC = tCustomProp.Parameters.SetAt("255","MAXLEN")
				Quit:$$$ISERR(tSC)
			}
			Set tDefault = tPropInfo."__getitem__"(2)
			If ""'=tDefault {
				Set tCustomProp.InitialExpression = $$$quote(tDefault)
				if $LENGTH(tDefault)>255 {
					Set tSC = tCustomProp.Parameters.SetAt("","MAXLEN")
					Quit:$$$ISERR(tSC)
				}
			}
			Set tCustomProp.Required = tPropInfo."__getitem__"(3)
			
			Set tSC = tCOSClass.Properties.Insert(tCustomProp)
			Quit:$$$ISERR(tSC)

			Set tPropCat = "Python Attributes $type"
			Set tSETTINGSParamValue = tSETTINGSParamValue_","_tPropName_":"_tPropCat
		}
		Quit:$$$ISERR(tSC)

		set type = ""
		set:($Case(tSuperClass,"IOP.InboundAdapter":1,"IOP.OutboundAdapter":1,:0)) type = "Adapter"
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

ClassMethod CreateProduction(
	package As %String = "test",
	name As %String = "AutoCreatedProduction",
	xdata As %CharacterStream) As %Status
{
  #Dim produtionClassName As %String = package _ "." _ name
  If ('$ZName(produtionClassName, 4))
  {
  Return $System.Status.Error(5001, "Invalid Production package or name.")
  }
  #Dim productionDefinition As %Dictionary.ClassDefinition
  // Check if the production already exists
  If (##class(%Dictionary.ClassDefinition).%ExistsId(produtionClassName))
  {
	// Open the production
	set productionDefinition = ##class(%Dictionary.ClassDefinition).%OpenId(produtionClassName)
  }
  Else
  {
	// Create the production definition
    set productionDefinition = ##Class(%Dictionary.ClassDefinition).%New()
  }
  //
  Set productionDefinition.Name         = produtionClassName
  Set productionDefinition.Super        = "Ens.Production"
  Set productionDefinition.ClassVersion = 25
  //
  // Check if the XData Definition already exists
  If (##Class(%Dictionary.XDataDefinition).%ExistsId(produtionClassName_"||ProductionDefinition"))
  {
	// delete the XData Definition
	$$$ThrowOnError(##Class(%Dictionary.XDataDefinition).%DeleteId(produtionClassName_"||ProductionDefinition"))
  }
  #Dim xdataDefinition As %Dictionary.XDataDefinition = ##Class(%Dictionary.XDataDefinition).%New()
  //
  Set xdataDefinition.Name = "ProductionDefinition"
  //
  Do xdataDefinition.Data.CopyFrom(xdata)
  //
  // Insert XData Definition into Production Definition
  Do productionDefinition.XDatas.Insert(xdataDefinition)
  //
  #Dim statusCode As %Status = productionDefinition.%Save()
  //
  If ($System.Status.IsError(statusCode))
  {
  Return statusCode
  }
  // Compile the production class
  return $System.OBJ.Compile(produtionClassName,"k-d")
}

/// Export a production to an XML string
ClassMethod ExportProduction(pProductionName As %String) As %String
{
	Set sc = $$$OK
	set xdata = ""
	// Check if the XData Definition exists
	If (##Class(%Dictionary.XDataDefinition).%ExistsId(pProductionName_"||ProductionDefinition"))
	{
		// Open the XData Definition
		Set xdataDefinition = ##Class(%Dictionary.XDataDefinition).%OpenId(pProductionName_"||ProductionDefinition")
		Set xdata = xdataDefinition.Data
	}
	Else
	{
		$$$ThrowOnError($System.Status.Error(5001, "Production does not exist."))
	}
	Return xdata
}

ClassMethod dispatchTestComponent(
	pTargetName As %String,
	pInput As Ens.Request) As Ens.Response
{
    #dim tService as EnsLib.Testing.Service
	set tOutput = ""
    $$$ThrowOnError(##class(Ens.Director).CreateBusinessService("EnsLib.Testing.Service", .tService))
    $$$ThrowOnError(tService.SendTestRequest(pTargetName, pInput, .tOutput, .sessionID , 1))
	Quit tOutput
}

}
