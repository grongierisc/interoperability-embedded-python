Class UnitTest.SimpleMessageSetVDoc Extends Ens.DataTransformDTL [ DependsOn = (IOP.Message, IOP.Message) ]
{

Parameter GENERATEEMPTYSEGMENTS = 0;

Parameter IGNOREMISSINGSOURCE = 1;

Parameter REPORTERRORS = 1;

Parameter TREATEMPTYREPEATINGFIELDASNULL = 0;

XData DTL [ XMLNamespace = "http://www.intersystems.com/dtl" ]
{
<transform sourceClass='IOP.Message' targetClass='IOP.Message' sourceDocType='registerFilesIop.message.SimpleMessage' targetDocType='registerFilesIop.message.SimpleMessage' create='new' language='objectscript' >
<assign value='source.{string}' property='target.{string}' action='set' />
<assign value='source.{integer}' property='target.{integer}' action='set' />
</transform>
}

}
