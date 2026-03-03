Class UnitTest.SimpleMessageSet Extends Ens.DataTransformDTL [ DependsOn = (IOP.Message, IOP.Message) ]
{

Parameter GENERATEEMPTYSEGMENTS = 0;

Parameter IGNOREMISSINGSOURCE = 1;

Parameter REPORTERRORS = 1;

Parameter TREATEMPTYREPEATINGFIELDASNULL = 0;

XData DTL [ XMLNamespace = "http://www.intersystems.com/dtl" ]
{
<transform sourceClass='Ens.StringRequest' targetClass='IOP.Message' sourceDocType='fixtures.message.SimpleMessage' targetDocType='fixtures.message.SimpleMessage' create='new' language='objectscript' >
<assign value='source.StringValue' property='target.{string}' action='set' />
</transform>
}

}
