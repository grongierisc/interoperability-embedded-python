Class Demo.PEX.NonProduction Extends %RegisteredObject
{

ClassMethod WrapperDemo() As %Status
{

    // Import the module
    set tModule = ##class(IOP.Wrapper).Import("my_script", "/irisdev/app/demo/python/non_production", 54132)
    
    // Call the function
    set result = tModule.main()

    // Print the result
    write result
}

ClassMethod WithoutWrapperDemo() As %Status
{

    // Set the Python path
    set sys = ##class(%SYS.Python).Import("sys")
    do sys."path"."append"("/irisdev/app/demo/python/non_production")

    // Import the module directly
    set tModule = ##class(%SYS.Python).Import("my_script")

    // Call the function
    set result = tModule.main()

    // Print the result
    write result
}

}
