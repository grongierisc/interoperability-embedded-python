Class UnitTest.SimpleMessageGet Extends Ens.DataTransformDTL [ DependsOn = (IOP.Message, Ens.StringResponse) ]
{

Parameter GENERATEEMPTYSEGMENTS = 0;

Parameter IGNOREMISSINGSOURCE = 1;

Parameter REPORTERRORS = 1;

Parameter TREATEMPTYREPEATINGFIELDASNULL = 0;

XData DTL [ XMLNamespace = "http://www.intersystems.com/dtl" ]
{
<transform sourceClass='IOP.Message' targetClass='Ens.StringResponse' sourceDocType='fixtures.message.SimpleMessage' targetDocType='fixtures.message.SimpleMessage' create='new' language='objectscript' >
<assign value='source.{string}' property='target.StringValue' action='set' />
</transform>
}

}
