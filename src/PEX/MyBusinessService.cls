Class PEX.MyBusinessService Extends Grongier.PEX.BusinessService [ GeneratedBy = Grongier.PEX.Utils ]
{

Parameter SETTINGS = "-%classname,-%settings,-%module,-%classpaths,-%useAdapterConnection";

Parameter ADAPTER;

Property %classname As %String [ InitialExpression = "MyBusinessService", Internal ];

/// One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Remote Gateway
Property %classpaths As %String(MAXLEN = "") [ InitialExpression = "/irisdev/app/src/python/demo/" ];

Property %module As %String [ InitialExpression = "MyBusinessService", Internal ];

Method SetPropertyValues()
{
	quit
}

}
