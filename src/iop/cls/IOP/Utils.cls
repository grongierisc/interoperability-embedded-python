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
	pProxyClassname As %String = "",
	pPythonLib,
	pPythonPath,
	pPythonVersion) As %Status
{
	set tSc = $$$OK
	$$$ThrowOnError(##class(IOP.Utils).RegisterComponent(pModule, pRemoteClassname, pCLASSPATHS, pFullpath, pOverwrite , pProxyClassname,pPythonLib, pPythonPath, pPythonVersion))
	return tSc
}

/// "bo","Duplex","/irisdev/app/src/python/demo/duplex/",1,"Duplex.Duplex"
ClassMethod RegisterComponent(
	pModule As %String,
	pRemoteClassname As %String,
	pCLASSPATHS As %String = "",
	pFullpath As %String = "",
	pOverwrite As %Boolean = 0,
	pProxyClassname As %String = "",
	pPythonLib,
	pPythonPath,
	pPythonVersion) As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tLanguage,tExtraClasspaths,tDelimiter,tOnePath As %String = ""
	#dim tClassDetails,tRemoteSettings As %String = ""
	#dim tClasspaths As %ListOfDataTypes
	
	Quit:(""=pRemoteClassname) $$$ERROR($$$EnsErrGeneral,"Remote Classname must be specified in order to register a Production EXtensions component")
	Quit:(""=pModule) $$$ERROR($$$EnsErrGeneral,"Must specify the module of the remote code.")
		
	Try {
		LOCK +^PythonSettings:10
		// Set the Python settings
		do ..SetPythonSettings(pPythonLib, pPythonPath, pPythonVersion)

		$$$ThrowOnError(..GetRemoteClassInfo(pRemoteClassname,pModule,pCLASSPATHS,pFullpath,.tClassDetails,.tRemoteSettings))

		Set tConnectionSettings("Classpaths") = pCLASSPATHS
		Set tConnectionSettings("Module") = pModule
		Set tConnectionSettings("Classname") = pRemoteClassname
		Set:(""=pProxyClassname) pProxyClassname = "User."_pRemoteClassname
		
		$$$ThrowOnError(..GenerateProxyClass(pProxyClassname,.tConnectionSettings,tClassDetails,tRemoteSettings,pOverwrite, pPythonLib, pPythonPath, pPythonVersion))

	} Catch ex {
		set msg = $System.Status.GetOneStatusText(ex.AsStatus(),1)
		set tSC = $$$ERROR($$$EnsErrGeneral,msg)
	}
	LOCK -PythonSettings
	Quit tSC
}

ClassMethod DeleteComponentProxy(pClassname As %String = "") As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tIsIOP As %Boolean = 0
	#dim tClass As %Dictionary.CompiledClass
	#dim tReferences As %DynamicArray
	
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
		If 'tIsIOP {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Cannot delete class '%1' because it is not a IOP proxy class.",pClassname))
			Quit
		}
		$$$ThrowOnError(..FindComponentProxyReferences(pClassname,.tReferences))
		If tReferences.%Size() > 0 {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Cannot delete class '%1' because it is used by production items: %2.",pClassname,..FormatComponentProxyReferences(tReferences)))
			Quit
		}
		Set tSC = ##class(%Dictionary.ClassDefinition).%DeleteId(pClassname)
		If $$$ISERR(tSC) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,$$$FormatText("Unable to delete proxy class for remote class '%1' : '%2'.",pClassname,$System.Status.GetErrorText(tSC)))
			Quit
		}
		
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	
	Quit tSC
}

ClassMethod FindComponentProxyReferences(
	pClassname As %String,
	ByRef pReferences) As %Status [ Internal ]
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	Set pReferences = []
	Quit:(""=pClassname) $$$ERROR($$$EnsErrGeneral,"Remote class name must be specified.")
	Try {
		Set tRS = ##class(%ResultSet).%New("Ens.Config.Production:ProductionStatus")
		$$$ThrowOnError(tRS.Execute())
		While tRS.Next() {
			$$$ThrowOnError(..CollectProductionProxyReferences(tRS.Data("Production"),pClassname,.pReferences))
		}
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	Quit tSC
}

ClassMethod CollectProductionProxyReferences(
	pProductionName As %String,
	pClassname As %String,
	ByRef pReferences) As %Status [ Internal, Private ]
{
	#dim tProduction As Ens.Config.Production
	#dim tItem As Ens.Config.Item
	Set tProduction = ##class(Ens.Config.Production).%OpenId(pProductionName)
	If '$IsObject(tProduction) {
		Set tLoaded = ##class(Ens.Config.Production).LoadFromClass(pProductionName)
		If $IsObject(tLoaded) {
			Set tProduction = tLoaded
		}
	}
	If '$IsObject(tProduction) {
		Quit $$$OK
	}
	For i=1:1:tProduction.Items.Count() {
		Set tItem = tProduction.Items.GetAt(i)
		If '$IsObject(tItem) Continue
		If tItem.ClassName = pClassname {
			Set tReference = {}
			Set tReference.production = pProductionName
			Set tReference.item = tItem.Name
			Do pReferences.%Push(tReference)
		}
	}
	Quit $$$OK
}

ClassMethod FormatComponentProxyReferences(pReferences As %DynamicArray) As %String [ Internal, Private ]
{
	Set tValue = ""
	For i=0:1:pReferences.%Size()-1 {
		Set tReference = pReferences.%Get(i)
		Set tValue = tValue_$Select(tValue="":"",1:", ")_tReference.production_"/"_tReference.item
	}
	Quit tValue
}

ClassMethod ListComponentProxies(pUnusedOnly As %Boolean = 0) As %String
{
	#dim ex As %Exception.AbstractException
	Set tResult = []
	Try {
		Set tStmt = ##class(%SQL.Statement).%New()
		$$$ThrowOnError(tStmt.%Prepare("SELECT Name FROM %Dictionary.ClassDefinition WHERE GeneratedBy = ? ORDER BY Name"))
		Set tRS = tStmt.%Execute("IOP.Utils")
		While tRS.%Next() {
			Set tClassname = tRS.%Get("Name")
			If '$classmethod(tClassname,"%Extends","IOP.Common") {
				Continue
			}
			$$$ThrowOnError(..FindComponentProxyReferences(tClassname,.tReferences))
			If pUnusedOnly {
				If tReferences.%Size() > 0 {
					Continue
				}
			}
			Set tEntry = {}
			Set tEntry."class" = tClassname
			Set tEntry.super = ..ProxySuperClass(tClassname)
			Set tEntry.module = ..ProxyPropertyInitialValue(tClassname,"%module")
			Set tEntry.classname = ..ProxyPropertyInitialValue(tClassname,"%classname")
			Set tEntry.classpaths = ..ProxyPropertyInitialValue(tClassname,"%classpaths")
			Set tEntry.used = (tReferences.%Size() > 0)
			Set tEntry."used_by" = tReferences
			Do tResult.%Push(tEntry)
		}
	} Catch ex {
		$$$ThrowOnError(ex.AsStatus())
	}
	Quit tResult.%ToJSON()
}

ClassMethod ProxySuperClass(pClassname As %String) As %String [ Internal, Private ]
{
	Set tClass = ##class(%Dictionary.ClassDefinition).%OpenId(pClassname)
	If '$IsObject(tClass) {
		Quit ""
	}
	Quit tClass.Super
}

ClassMethod ProxyPropertyInitialValue(
	pClassname As %String,
	pProperty As %String) As %String [ Internal, Private ]
{
	Set tStmt = ##class(%SQL.Statement).%New()
	$$$ThrowOnError(tStmt.%Prepare("SELECT InitialExpression FROM %Dictionary.PropertyDefinition WHERE parent = ? AND name = ?"))
	Set tRS = tStmt.%Execute(pClassname,pProperty)
	If tRS.%Next() {
		Quit ..UnquoteInitialExpression(tRS.%Get("InitialExpression"))
	}
	Quit ""
}

ClassMethod UnquoteInitialExpression(pValue As %String) As %String [ Internal, Private ]
{
	Set tValue = $Get(pValue)
	If ($Extract(tValue,1)="""")&&($Extract(tValue,*)="""") {
		Set tValue = $Extract(tValue,2,*-1)
	}
	Quit tValue
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
		// Allocate without calling Python __init__. Registration only reads
		// metadata; runtime startup belongs in on_init().
		set tClass = class."__new__"(class)
		Try {
			Do tClass."_warn_if_custom_init"()
		}
		Catch ex {
		}

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
	pOverwrite As %Boolean = 0,
	pPythonLib,
	pPythonPath,
	pPythonVersion) As %Status [ Internal, Private ]
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
 		#dim tSETTINGSParamValue As %String = "%classname:Python $type,%module:Python $type,%settings:Python $type,%classpaths:Python $type:directorySelector"
		set tSETTINGSParamValue = tSETTINGSParamValue_","_"%enable:Python Debug $type,%timeout:Python Debug $type,%port:Python Debug $type,%PythonInterpreterPath:Python Debug $type,%traceback:Python Debug $type"
		set tSETTINGSParamValue = tSETTINGSParamValue_","_"%PythonPath:Python Settings $type,%PythonRuntimeLibrary:Python Settings $type,%PythonRuntimeLibraryVersion:Python Settings $type,%Venv:Python Settings $type"
		
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

		if pPythonLib'="" {
			#dim tPropPythonLib As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
			Set tPropPythonLib.Name = "%PythonRuntimeLibrary"
			Set tPropPythonLib.Type = "%String"
			Set tPropPythonLib.Internal = 1
			Set tSC = tPropPythonLib.Parameters.SetAt("","MAXLEN")
			Quit:$$$ISERR(tSC)
			Set tPropPythonLib.InitialExpression = $$$quote(pPythonLib)
			Set tSC = tCOSClass.Properties.Insert(tPropPythonLib)
			Quit:$$$ISERR(tSC)
		}
		if pPythonPath'="" {
			#dim tPropPythonPath As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
			Set tPropPythonPath.Name = "%PythonPath"
			Set tPropPythonPath.Type = "%String"
			Set tSC = tPropPythonPath.Parameters.SetAt("","MAXLEN")
			Quit:$$$ISERR(tSC)
			Set tPropPythonPath.Internal = 1
			Set tPropPythonPath.InitialExpression = $$$quote(pPythonPath)
			Set tSC = tCOSClass.Properties.Insert(tPropPythonPath)
			Quit:$$$ISERR(tSC)
		}
		if pPythonVersion'="" {
			#dim tPropPythonVersion As %Dictionary.PropertyDefinition = ##class(%Dictionary.PropertyDefinition).%New()
			Set tPropPythonVersion.Name = "%PythonRuntimeLibraryVersion"
			Set tPropPythonVersion.Type = "%String"
			Set tPropPythonVersion.Internal = 1
			Set tPropPythonVersion.InitialExpression = $$$quote(pPythonVersion)
			Set tSC = tCOSClass.Properties.Insert(tPropPythonVersion)
			Quit:$$$ISERR(tSC)
		}
		
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
			Set tDesc = ""
			If (builtins.len(tPropInfo)>5) {
				Set tDesc = tPropInfo."__getitem__"(5)
			}
			If ""'=tDesc {
				Set tCustomProp.Description = tDesc
			}
			
			Set tSC = tCOSClass.Properties.Insert(tCustomProp)
			Quit:$$$ISERR(tSC)

			Set tPropCat = ""
			If (builtins.len(tPropInfo)>4) {
				Set tPropCat = tPropInfo."__getitem__"(4)
			}
			If ""=tPropCat {
				Set tPropCat = "Python Attributes $type"
			}
			Set tContext = ""
			If (builtins.len(tPropInfo)>6) {
				Set tContext = tPropInfo."__getitem__"(6)
			}
			Set tSETTINGSParamValue = tSETTINGSParamValue_","_tPropName_":"_tPropCat
			If ""'=tContext {
				Set tSETTINGSParamValue = tSETTINGSParamValue_":"_tContext
			}
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

ClassMethod CreateProductionFromJSON(
	pProductionName As %String,
	pDefinition As %String) As %Status
{
	#dim tSC As %Status = $$$OK
	#dim ex As %Exception.AbstractException
	#dim tPayload As %DynamicObject
	#dim tProductionData As %DynamicObject
	#dim tProduction As Ens.Config.Production
	#dim tProductionClass As %Dictionary.ClassDefinition
	#dim tItems,tDeclaredName
	Try {
		Return:(""=pProductionName) $$$ERROR($$$EnsErrGeneral,"Production name is required.")
		Return:('$ZName(pProductionName,4)) $$$ERROR($$$EnsErrGeneral,"Invalid Production name.")

		Set tPayload = {}.%FromJSON(pDefinition)
		Set tProductionData = tPayload.%Get("Production")
		If '$IsObject(tProductionData) {
			Set tSC = $$$ERROR($$$EnsErrGeneral,"Production JSON must contain a Production object.")
			Quit
		}
		Set tDeclaredName = ..DynamicGet(tProductionData,"@Name","")
		If ""'=tDeclaredName {
			If pProductionName'=tDeclaredName {
				Set tSC = $$$ERROR($$$EnsErrGeneral,"Production JSON name does not match target production name.")
				Quit
			}
		}

		If ('##class(%Dictionary.ClassDefinition).%ExistsId(pProductionName)) {
			Set tProductionClass = ##class(%Dictionary.ClassDefinition).%New()
			Set tProductionClass.Name = pProductionName
			Set tProductionClass.Super = "Ens.Production"
			Set tProductionClass.ClassVersion = 25
			Set tSC = tProductionClass.%Save()
			Quit:$$$ISERR(tSC)
		}

		Set tProduction = ##class(Ens.Config.Production).%New()
		Set tProduction.Name = pProductionName
		Set tProduction.Description = ..DynamicGet(tProductionData,"Description","")
		Set tProduction.ActorPoolSize = +..DynamicGet(tProductionData,"ActorPoolSize",2)
		Set tProduction.TestingEnabled = ..BooleanValue(..DynamicGet(tProductionData,"@TestingEnabled",0))
		Set tProduction.LogGeneralTraceEvents = ..BooleanValue(..DynamicGet(tProductionData,"@LogGeneralTraceEvents",0))

		$$$ThrowOnError(..InsertSettings(tProduction,tProductionData.%Get("Setting")))
		Set tItems = tProductionData.%Get("Item")
		$$$ThrowOnError(..InsertItems(tProduction,tItems))

		Set tSC = tProduction.SaveToClass()
		Quit:$$$ISERR(tSC)
		Set tSC = $System.OBJ.Compile(pProductionName,"k-d")
	} Catch ex {
		Set tSC = ex.AsStatus()
	}
	Quit tSC
}

ClassMethod DynamicGet(pObject, pName As %String, pDefault = "") [ Internal, Private ]
{
	#dim value
	Try {
		Set value = pObject.%Get(pName)
	} Catch ex {
		Return pDefault
	}
	Quit $Select(value="":pDefault,1:value)
}

ClassMethod BooleanValue(pValue) As %Boolean [ Internal, Private ]
{
	Set tValue = $ZCONVERT(pValue,"L")
	Quit $Select(tValue="true":1,tValue="1":1,tValue="yes":1,tValue="on":1,tValue="false":0,tValue="0":0,tValue="no":0,tValue="off":0,1:+pValue)
}

ClassMethod IsDynamicArray(pValue) As %Boolean [ Internal, Private ]
{
	Quit $Select('$IsObject(pValue):0,pValue.%ClassName(1)="%Library.DynamicArray":1,1:0)
}

ClassMethod InsertItems(
	pProduction As Ens.Config.Production,
	pItems) As %Status [ Internal, Private ]
{
	#dim tSC As %Status = $$$OK
	If '$IsObject(pItems) {
		Quit tSC
	}
	If ..IsDynamicArray(pItems) {
		For i=0:1:pItems.%Size()-1 {
			$$$ThrowOnError(..InsertItem(pProduction,pItems.%Get(i)))
		}
	} Else {
		$$$ThrowOnError(..InsertItem(pProduction,pItems))
	}
	Quit tSC
}

ClassMethod InsertItem(
	pProduction As Ens.Config.Production,
	pItemData) As %Status [ Internal, Private ]
{
	#dim tItem As Ens.Config.Item
	Set tItem = ##class(Ens.Config.Item).%New()
	Set tItem.Name = ..DynamicGet(pItemData,"@Name","")
	Set tItem.ClassName = ..DynamicGet(pItemData,"@ClassName","")
	Set tItem.Category = ..DynamicGet(pItemData,"@Category","")
	Set tItem.PoolSize = +..DynamicGet(pItemData,"@PoolSize",0)
	Set tItem.Enabled = ..BooleanValue(..DynamicGet(pItemData,"@Enabled",1))
	Set tItem.Foreground = ..BooleanValue(..DynamicGet(pItemData,"@Foreground",0))
	Set tItem.Comment = ..DynamicGet(pItemData,"@Comment","")
	Set tItem.LogTraceEvents = ..BooleanValue(..DynamicGet(pItemData,"@LogTraceEvents",0))
	Set tItem.Schedule = ..DynamicGet(pItemData,"@Schedule","")
	Set tItem.Production = pProduction

	$$$ThrowOnError(..InsertSettings(tItem,pItemData.%Get("Setting")))
	Do pProduction.Items.Insert(tItem)
	Quit $$$OK
}

ClassMethod InsertSettings(
	pOwner,
	pSettings) As %Status [ Internal, Private ]
{
	#dim tSC As %Status = $$$OK
	If '$IsObject(pSettings) {
		Quit tSC
	}
	If ..IsDynamicArray(pSettings) {
		For i=0:1:pSettings.%Size()-1 {
			$$$ThrowOnError(..InsertSetting(pOwner,pSettings.%Get(i)))
		}
	} Else {
		$$$ThrowOnError(..InsertSetting(pOwner,pSettings))
	}
	Quit tSC
}

ClassMethod InsertSetting(
	pOwner,
	pSettingData) As %Status [ Internal, Private ]
{
	#dim tSetting As Ens.Config.Setting
	#dim tDefaultTarget As %String
	Set tDefaultTarget = $Select(pOwner.%IsA("Ens.Config.Production"):"",1:"Host")
	Set tSetting = ##class(Ens.Config.Setting).%New()
	Set tSetting.Target = ..DynamicGet(pSettingData,"@Target",tDefaultTarget)
	Set tSetting.Name = ..DynamicGet(pSettingData,"@Name","")
	Set tSetting.Value = ..DynamicGet(pSettingData,"#text","")
	Do pOwner.Settings.Insert(tSetting)
	Quit $$$OK
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

/// Export runtime production connections discovered through OnGetConnections.
ClassMethod ExportProductionConnections(pProductionName As %String) As %String
{
	Set result = {}
	Set result.production = pProductionName
	Set result.items = []
	Set result.warnings = []
	Try {
		Set production = ##class(Ens.Config.Production).%OpenId(pProductionName)
		If '$IsObject(production) {
			Set loaded = ##class(Ens.Config.Production).LoadFromClass(pProductionName)
			If $IsObject(loaded) {
				Set production = loaded
			} Else {
				Set warning = "Production could not be loaded: "_pProductionName
				If loaded'="" {
					Try {
						If $System.Status.IsError(loaded) {
							Set warning = warning_": "_$System.Status.GetOneStatusText(loaded)
						}
					} Catch exStatus {
					}
				}
				Do result.warnings.%Push(warning)
				Return result.%ToJSON()
			}
		}
		For i=1:1:production.Items.Count() {
			Set item = production.Items.GetAt(i)
			If '$IsObject(item) Continue
			Set itemResult = {}
			Set itemResult.item = item.Name
			Set itemResult."class_name" = item.ClassName
			Set adapterClass = ""
			Try {
				Set adapterClass = $Parameter(item.ClassName, "ADAPTER")
			} Catch exAdapter {
			}
			If adapterClass '= "" {
				Set itemResult."adapter_class_name" = adapterClass
			}
			Set itemResult.connections = []
			Set itemResult.warnings = []
			Try {
				Kill connections
				Do ##class(Ens.Config.Production).GetConnections(.connections,item.ClassName,item)
				Set target = ""
				For {
					Set target = $Order(connections(target))
					Quit:target=""
					Do itemResult.connections.%Push(target)
				}
			} Catch ex {
				Do itemResult.warnings.%Push(ex.DisplayString())
			}
			Do result.items.%Push(itemResult)
		}
	} Catch ex {
		Do result.warnings.%Push(ex.DisplayString())
	}
	Return result.%ToJSON()
}

/// Export queue counters for production items.
ClassMethod ExportProductionQueueInfo(pProductionName As %String) As %String
{
	Set result = {}
	Set result.production = pProductionName
	Set result.items = []
	Set result.warnings = []
	Try {
		Set production = ##class(Ens.Config.Production).%OpenId(pProductionName)
		If '$IsObject(production) {
			Set loaded = ##class(Ens.Config.Production).LoadFromClass(pProductionName)
			If $IsObject(loaded) {
				Set production = loaded
			} Else {
				Set warning = "Production could not be loaded: "_pProductionName
				If loaded'="" {
					Try {
						If $System.Status.IsError(loaded) {
							Set warning = warning_": "_$System.Status.GetOneStatusText(loaded)
						}
					} Catch exStatus {
					}
				}
				Do result.warnings.%Push(warning)
				Return result.%ToJSON()
			}
		}
		For i=1:1:production.Items.Count() {
			Set item = production.Items.GetAt(i)
			If '$IsObject(item) Continue
			Set itemResult = {}
			Set itemResult.item = item.Name
			Set itemResult."queue_name" = item.Name
			Set itemResult."class_name" = item.ClassName
			Set queueCount = ##class(Ens.Queue).GetCount(item.Name)
			If queueCount="" {
				Set itemResult.exists = 0
				Set itemResult.count = 0
			} Else {
				Set itemResult.exists = 1
				Set itemResult.count = +queueCount
			}
			Do result.items.%Push(itemResult)
		}
	} Catch ex {
		Do result.warnings.%Push(ex.DisplayString())
	}
	Return result.%ToJSON()
}

/// Apply a conservative granular production change plan.
ClassMethod ApplyProductionPlan(
	pProductionName As %String,
	pPlan As %String,
	pAllowDestructive As %Boolean = 0) As %String
{
	Set result = {}
	Set result.production = pProductionName
	Set result.operations = []
	Try {
		Set plan = {}.%FromJSON(pPlan)
		Set operations = plan.%Get("operations")
		Set production = ##class(Ens.Config.Production).%OpenId(pProductionName)
		If '$IsObject(production) {
			Set loaded = ##class(Ens.Config.Production).LoadFromClass(pProductionName)
			If $IsObject(loaded) {
				Set production = loaded
			} Else {
				$$$ThrowStatus($$$ERROR($$$EnsErrGeneral,"Production could not be loaded: "_pProductionName))
			}
		}
		If $IsObject(operations) {
			For i=0:1:operations.%Size()-1 {
				Set operation = operations.%Get(i)
				Set opResult = {}
				Set opResult.id = operation.%Get("id")
				Set opResult."op_type" = operation.%Get("op_type")
				Set opResult.path = operation.%Get("path")
				Set risk = operation.%Get("risk")
				If risk = "unsupported" {
					Set opResult.status = "skipped"
					Set opResult.message = $Select(operation.%Get("reason")'="":operation.%Get("reason"),1:"unsupported operation")
				} ElseIf (risk = "destructive") && ('pAllowDestructive) {
					Set opResult.status = "skipped"
					Set opResult.message = "requires allow_destructive"
				} Else {
					Try {
						$$$ThrowOnError(..ApplyProductionPlanOperation(production, operation))
						Set opResult.status = "applied"
					} Catch opEx {
						Set opResult.status = "failed"
						Set opResult.message = opEx.DisplayString()
					}
				}
				Do result.operations.%Push(opResult)
			}
		}
		$$$ThrowOnError(production.SaveToClass())
		$$$ThrowOnError($System.OBJ.Compile(pProductionName,"k-d"))
	} Catch ex {
		Set result.error = ex.DisplayString()
	}
	Return result.%ToJSON()
}

ClassMethod ApplyProductionPlanOperation(
	pProduction As Ens.Config.Production,
	pOperation) As %Status [ Internal, Private ]
{
	Set opType = pOperation.%Get("op_type")
	If opType = "add_item" {
		Return ..ApplyPlanAddItem(pProduction,pOperation)
	}
	If opType = "delete_item" {
		Return ..ApplyPlanDeleteItem(pProduction,pOperation.%Get("item"))
	}
	If opType = "set_item_field" {
		Return ..ApplyPlanSetItemField(pProduction,pOperation)
	}
	If opType = "replace_item_class" {
		Return ..ApplyPlanSetItemField(pProduction,pOperation)
	}
	If opType = "set_production_field" {
		Return ..ApplyPlanSetProductionField(pProduction,pOperation)
	}
	If opType = "set_setting" {
		If pOperation.%Get("target") = "Other" {
			Return ..ReplaceOtherSettings(..FindProductionItem(pProduction,pOperation.%Get("item")),pOperation.%Get("after"))
		}
		Return ..SetConfigSetting(..FindProductionItem(pProduction,pOperation.%Get("item")),pOperation.%Get("target"),pOperation.%Get("setting"),pOperation.%Get("after"))
	}
	If opType = "remove_setting" {
		Return ..RemoveConfigSetting(..FindProductionItem(pProduction,pOperation.%Get("item")),pOperation.%Get("target"),pOperation.%Get("setting"))
	}
	If opType = "set_route_setting" {
		Return ..SetConfigSetting(..FindProductionItem(pProduction,pOperation.%Get("source_item")),"Host",pOperation.%Get("source_target_setting"),..DynamicArrayToCSV(pOperation.%Get("after")))
	}
	If opType = "remove_route" {
		Return ..RemoveConfigSetting(..FindProductionItem(pProduction,pOperation.%Get("source_item")),"Host",pOperation.%Get("source_target_setting"))
	}
	Quit $$$ERROR($$$EnsErrGeneral,"Unsupported production plan operation: "_opType)
}

ClassMethod ApplyPlanAddItem(
	pProduction As Ens.Config.Production,
	pOperation) As %Status [ Internal, Private ]
{
	Set itemName = pOperation.%Get("item")
	If itemName = "" {
		Quit $$$ERROR($$$EnsErrGeneral,"Plan item name is required.")
	}
	If $IsObject(..FindProductionItem(pProduction,itemName,0)) {
		Quit $$$ERROR($$$EnsErrGeneral,"Production item already exists: "_itemName)
	}
	Set data = pOperation.%Get("after")
	Set item = ##class(Ens.Config.Item).%New()
	Set item.Name = itemName
	Set item.ClassName = data.%Get("class_name")
	Set item.Category = data.%Get("category")
	Set item.PoolSize = +data.%Get("pool_size")
	Set item.Enabled = ..BooleanValue(data.%Get("enabled"))
	Set item.Foreground = ..BooleanValue(data.%Get("foreground"))
	Set item.Comment = data.%Get("comment")
	Set item.LogTraceEvents = ..BooleanValue(data.%Get("log_trace_events"))
	Set item.Schedule = data.%Get("schedule")
	Set item.Production = pProduction
	$$$ThrowOnError(..SetSettingsFromMap(item,"Host",data.%Get("host_settings")))
	$$$ThrowOnError(..SetSettingsFromMap(item,"Adapter",data.%Get("adapter_settings")))
	$$$ThrowOnError(..ReplaceOtherSettings(item,data.%Get("other_settings")))
	Do pProduction.Items.Insert(item)
	Quit $$$OK
}

ClassMethod ApplyPlanDeleteItem(
	pProduction As Ens.Config.Production,
	pItemName As %String) As %Status [ Internal, Private ]
{
	Set index = ..FindProductionItemIndex(pProduction,pItemName)
	If index < 1 {
		Quit $$$OK
	}
	Do pProduction.Items.RemoveAt(index)
	Quit $$$OK
}

ClassMethod ApplyPlanSetItemField(
	pProduction As Ens.Config.Production,
	pOperation) As %Status [ Internal, Private ]
{
	Set item = ..FindProductionItem(pProduction,pOperation.%Get("item"))
	Set field = pOperation.%Get("field")
	Set value = pOperation.%Get("after")
	If field = "class_name" {
		Set item.ClassName = value
	} ElseIf field = "category" {
		Set item.Category = value
	} ElseIf field = "pool_size" {
		Set item.PoolSize = +value
	} ElseIf field = "enabled" {
		Set item.Enabled = ..BooleanValue(value)
	} ElseIf field = "foreground" {
		Set item.Foreground = ..BooleanValue(value)
	} ElseIf field = "comment" {
		Set item.Comment = value
	} ElseIf field = "log_trace_events" {
		Set item.LogTraceEvents = ..BooleanValue(value)
	} ElseIf field = "schedule" {
		Set item.Schedule = value
	} Else {
		Quit $$$ERROR($$$EnsErrGeneral,"Unsupported item field: "_field)
	}
	Quit $$$OK
}

ClassMethod ApplyPlanSetProductionField(
	pProduction As Ens.Config.Production,
	pOperation) As %Status [ Internal, Private ]
{
	Set field = pOperation.%Get("field")
	Set value = pOperation.%Get("after")
	If field = "testing_enabled" {
		Set pProduction.TestingEnabled = ..BooleanValue(value)
	} ElseIf field = "log_general_trace_events" {
		Set pProduction.LogGeneralTraceEvents = ..BooleanValue(value)
	} ElseIf field = "actor_pool_size" {
		Set pProduction.ActorPoolSize = +value
	} ElseIf field = "description" {
		Set pProduction.Description = value
	} Else {
		Set settingName = ..ProductionSettingName(field)
		If settingName = "" {
			Quit $$$ERROR($$$EnsErrGeneral,"Unsupported production field: "_field)
		}
		$$$ThrowOnError(..SetConfigSetting(pProduction,"",settingName,value))
	}
	Quit $$$OK
}

ClassMethod ProductionSettingName(pField As %String) As %String [ Internal, Private ]
{
	Quit $Select(
		pField="shutdown_timeout":"ShutdownTimeout",
		pField="update_timeout":"UpdateTimeout",
		pField="alert_notification_manager":"AlertNotificationManager",
		pField="alert_notification_operation":"AlertNotificationOperation",
		pField="alert_notification_recipients":"AlertNotificationRecipients",
		pField="alert_action_window":"AlertActionWindow",
		1:"")
}

ClassMethod FindProductionItem(
	pProduction As Ens.Config.Production,
	pItemName As %String,
	pThrow As %Boolean = 1) [ Internal, Private ]
{
	Set index = ..FindProductionItemIndex(pProduction,pItemName)
	If index > 0 {
		Quit pProduction.Items.GetAt(index)
	}
	If pThrow {
		$$$ThrowStatus($$$ERROR($$$EnsErrGeneral,"Production item does not exist: "_pItemName))
	}
	Quit ""
}

ClassMethod FindProductionItemIndex(
	pProduction As Ens.Config.Production,
	pItemName As %String) As %Integer [ Internal, Private ]
{
	For i=1:1:pProduction.Items.Count() {
		Set item = pProduction.Items.GetAt(i)
		If $IsObject(item), item.Name = pItemName {
			Return i
		}
	}
	Quit 0
}

ClassMethod SetSettingsFromMap(
	pOwner,
	pTarget As %String,
	pMap) As %Status [ Internal, Private ]
{
	If '$IsObject(pMap) {
		Quit $$$OK
	}
	Set iterator = pMap.%GetIterator()
	While iterator.%GetNext(.key,.value) {
		$$$ThrowOnError(..SetConfigSetting(pOwner,pTarget,key,value))
	}
	Quit $$$OK
}

ClassMethod SetConfigSetting(
	pOwner,
	pTarget As %String,
	pName As %String,
	pValue) As %Status [ Internal, Private ]
{
	Set index = ..FindConfigSettingIndex(pOwner,pTarget,pName)
	If index > 0 {
		Set setting = pOwner.Settings.GetAt(index)
	} Else {
		Set setting = ##class(Ens.Config.Setting).%New()
		Set setting.Target = pTarget
		Set setting.Name = pName
		Do pOwner.Settings.Insert(setting)
	}
	Set setting.Value = pValue
	Quit $$$OK
}

ClassMethod RemoveConfigSetting(
	pOwner,
	pTarget As %String,
	pName As %String) As %Status [ Internal, Private ]
{
	Set index = ..FindConfigSettingIndex(pOwner,pTarget,pName)
	If index > 0 {
		Do pOwner.Settings.RemoveAt(index)
	}
	Quit $$$OK
}

ClassMethod ReplaceOtherSettings(
	pOwner,
	pSettings) As %Status [ Internal, Private ]
{
	For i=pOwner.Settings.Count():-1:1 {
		Set setting = pOwner.Settings.GetAt(i)
		If $IsObject(setting), setting.Target '= "Host", setting.Target '= "Adapter" {
			Do pOwner.Settings.RemoveAt(i)
		}
	}
	If '$IsObject(pSettings) {
		Quit $$$OK
	}
	For i=0:1:pSettings.%Size()-1 {
		Set data = pSettings.%Get(i)
		Set setting = ##class(Ens.Config.Setting).%New()
		Set setting.Target = ..DynamicGet(data,"@Target","")
		Set setting.Name = ..DynamicGet(data,"@Name","")
		Set setting.Value = ..DynamicGet(data,"#text","")
		Do pOwner.Settings.Insert(setting)
	}
	Quit $$$OK
}

ClassMethod FindConfigSettingIndex(
	pOwner,
	pTarget As %String,
	pName As %String) As %Integer [ Internal, Private ]
{
	For i=1:1:pOwner.Settings.Count() {
		Set setting = pOwner.Settings.GetAt(i)
		If $IsObject(setting), setting.Target = pTarget, setting.Name = pName {
			Return i
		}
	}
	Quit 0
}

ClassMethod DynamicArrayToCSV(pArray) As %String [ Internal, Private ]
{
	If '$IsObject(pArray) {
		Quit pArray
	}
	Set value = ""
	For i=0:1:pArray.%Size()-1 {
		If value '= "" {
			Set value = value_","
		}
		Set value = value_pArray.%Get(i)
	}
	Quit value
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

ClassMethod SetPythonSettings(
	pPythonLib,
	pPythonPath,
	pPythonVersion) As %Status
{
    set currentNS = $namespace
    set $NAMESPACE = "%SYS"
	set tSC = $$$OK

    try {
        // Get Config
        $$$ThrowOnError(##Class(Config.config).Get(.Properties))
        // Set the Python interpreter path
        if pPythonPath'="" {
            set Properties("PythonPath") = pPythonPath
        }
    
        // Set the Python runtime library
        if pPythonLib'="" {
            set Properties("PythonRuntimeLibrary") = pPythonLib
        }
    
        // Set the Python runtime library version
        if pPythonVersion'="" {
            set Properties("PythonRuntimeLibraryVersion") = pPythonVersion
        }
        $$$ThrowOnError(##Class(Config.config).Modify(.Properties))
    } catch ex {
        set tSC = ex.AsStatus()
    }

    set $NAMESPACE = currentNS
	Quit tSC
}

}
