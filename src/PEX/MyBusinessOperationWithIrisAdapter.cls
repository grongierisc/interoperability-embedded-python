Class PEX.MyBusinessOperationWithIrisAdapter Extends Grongier.PEX.BusinessOperation [ GeneratedBy = Grongier.PEX.Utils ]
{

Parameter ADAPTER = "EnsLib.File.OutboundAdapter";

Parameter SETTINGS = "-%classname,-%settings,-%module,-%classpaths,-%useAdapterConnection";

Property %classname As %String [ InitialExpression = "MyBusinessOperationWithIrisAdapter", Internal ];

/// One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Remote Gateway
Property %classpaths As %String(MAXLEN = "") [ InitialExpression = "/irisdev/app/src/python/:/irisdev/app/src/python/demo" ];

Property %module As %String [ InitialExpression = "MyBusinessOperationWithIrisAdapter", Internal ];

Method SetPropertyValues()
{
	quit
}

}
