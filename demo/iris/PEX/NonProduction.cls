Class Demo.PEX.NonProduction Extends %RegisteredObject
{

ClassMethod WrapperDemo() As %Status
{

    // Import the module
    set tModule = ##class(IOP.Wrapper).Import("my_script", "/Users/grongier/git/interoperability-embedded-python/demo/python/non_production/", 54132)
    
    // Call the function
    do tModule.main()
}

}
