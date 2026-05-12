Include %occInclude

Class IOP.PersistentMessage.Registry Extends %RegisteredObject
{

ClassMethod Register(
	pPythonClass As %String,
	pIRISClass As %String) As %Status
{
	If pPythonClass = "" Quit $$$ERROR($$$GeneralError, "Python class is required")
	If pIRISClass = "" Quit $$$ERROR($$$GeneralError, "IRIS class is required")

	Set ^IOP.PersistentMessage.Registry("Python", pPythonClass) = pIRISClass
	Set ^IOP.PersistentMessage.Registry("IRIS", pIRISClass) = pPythonClass
	Quit $$$OK
}

ClassMethod GetIRISClassName(pPythonClass As %String = "") As %String
{
	Quit $Get(^IOP.PersistentMessage.Registry("Python", pPythonClass))
}

ClassMethod GetPythonClassName(pIRISClass As %String = "") As %String
{
	Quit $Get(^IOP.PersistentMessage.Registry("IRIS", pIRISClass))
}

ClassMethod GetPythonClassNameForObject(pObject As %RegisteredObject) As %String
{
	If '$IsObject(pObject) Quit ""
	Quit ..GetPythonClassName(pObject.%ClassName(1))
}

}
