Class UnitTest.ComplexTransform Extends Ens.DataTransformDTL [ DependsOn = IOP.Message ]
{

Parameter IGNOREMISSINGSOURCE = 1;

Parameter REPORTERRORS = 1;

Parameter TREATEMPTYREPEATINGFIELDASNULL = 0;

XData DTL [ XMLNamespace = "http://www.intersystems.com/dtl" ]
{
<transform sourceClass='IOP.Message' targetClass='IOP.Message' sourceDocType='registerFilesIop.message.ComplexMessage' targetDocType='registerFilesIop.message.ComplexMessage' create='new' language='objectscript' >
<assign value='source.{post}' property='target.{post}' action='set' />
<foreach property='source.{list_str()}' key='k1' >
<assign value='source.{list_str(k1)}_"foo"' property='target.{list_str()}' action='append' />
</foreach>
<foreach property='source.{list_post()}' key='k2' >
<assign value='source.{list_post().Title}' property='target.{list_post(k2).Title}' action='append' />
</foreach>
</transform>
}

}
