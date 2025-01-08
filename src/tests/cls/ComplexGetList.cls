Class UnitTest.ComplexGetList Extends Ens.DataTransformDTL [ DependsOn = (IOP.Message, Ens.StringRequest) ]
{

Parameter GENERATEEMPTYSEGMENTS = 0;

Parameter IGNOREMISSINGSOURCE = 1;

Parameter REPORTERRORS = 1;

Parameter TREATEMPTYREPEATINGFIELDASNULL = 0;

XData DTL [ XMLNamespace = "http://www.intersystems.com/dtl" ]
{
<transform sourceClass='IOP.Message' targetClass='Ens.StringRequest' sourceDocType='registerFilesIop.message.ComplexMessage' create='new' language='objectscript' >
<assign value='source.{list_post(2).Title}' property='target.StringValue' action='set' />
</transform>
}

}
