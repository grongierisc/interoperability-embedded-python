Class Demo.PEX.NonProduction Extends %RegisteredObject
{

ClassMethod WrapperDemo() As %Status
{

    // Import the module
    set tModule = ##class(IOP.Wrapper).Import("my_script", "/irisdev/app/demo/python/non_production/", 54132)
    
    // Call the function
    set result = tModule.main()

    // Print the result
    write result
}

}
