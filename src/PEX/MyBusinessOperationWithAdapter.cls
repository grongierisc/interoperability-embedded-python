Class PEX.MyBusinessOperationWithAdapter Extends Grongier.PEX.BusinessOperation [ GeneratedBy = Grongier.PEX.Utils ]
{

Parameter ADAPTER = "PEX.MyOutboundAdapter";

Parameter SETTINGS = "%classname:Python,%module:Python,%settings:Python,%classpaths:Python";

Property %classname As %String [ InitialExpression = "MyBusinessOperationWithAdapter", Internal ];

/// One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Remote Gateway
Property %classpaths As %String(MAXLEN = "") [ InitialExpression = "/irisdev/app/src/python/demo/" ];

Property %module As %String [ InitialExpression = "MyBusinessOperationWithAdapter", Internal ];

Method SetPropertyValues()
{
	quit
}

}
