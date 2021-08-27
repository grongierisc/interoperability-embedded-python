/// 
Class dc.Demo.FilterPostsRoutingRule Extends Ens.Rule.Definition
{

Parameter RuleAssistClass = "EnsLib.MsgRouter.RuleAssist";

XData RuleDefinition [ XMLNamespace = "http://www.intersystems.com/rule" ]
{
<ruleDefinition alias="" context="EnsLib.MsgRouter.RoutingEngine" production="dc.Demo.Production">
<ruleSet name="" effectiveBegin="" effectiveEnd="">
<rule name="">
<constraint name="msgClass" value="dc.Demo.PostMessage"></constraint>
<when condition="ToUpper(Document.Post.Selftext) Contains ToUpper(&quot;dog&quot;)">
<assign property="Document.ToEmailAddress" value="&quot;dog@company.com&quot;"></assign>
<assign property="Document.Found" value="&quot;Dog&quot;"></assign>
<send transform="" target="dc.Demo.FileOperation"></send>
<return></return>
</when>
<when condition="ToUpper(Document.Post.Selftext) Contains ToUpper(&quot;cat&quot;)">
<assign property="Document.ToEmailAddress" value="&quot;cat@company.com&quot;"></assign>
<assign property="Document.Found" value="&quot;Cat&quot;"></assign>
<send transform="" target="dc.Demo.FileOperation"></send>
<return></return>
</when>
<otherwise>
<return></return>
</otherwise>
</rule>
</ruleSet>
</ruleDefinition>
}

}
