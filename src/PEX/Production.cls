Class PEX.Production Extends Ens.Production
{

XData ProductionDefinition
{
<Production Name="PEX.Production" TestingEnabled="true" LogGeneralTraceEvents="true">
  <Description></Description>
  <ActorPoolSize>2</ActorPoolSize>
  <Item Name="Grongier.PEX.BusinessOperation" Category="" ClassName="Grongier.PEX.BusinessOperation" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="true" Schedule="">
    <Setting Target="Host" Name="%classname">MyBusinessOperation</Setting>
    <Setting Target="Host" Name="%classpaths">/irisdev/app/src/python/demo:/usr/irissys/mgr/python/pex</Setting>
    <Setting Target="Host" Name="%module">MyBusinessOperation</Setting>
  </Item>
  <Item Name="Grongier.PEX.BusinessService" Category="" ClassName="Grongier.PEX.BusinessService" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="true" Schedule="">
    <Setting Target="Host" Name="%classname">MyBusinessService</Setting>
    <Setting Target="Host" Name="%classpaths">/irisdev/app/src/python/demo:/usr/irissys/mgr/python/pex</Setting>
    <Setting Target="Host" Name="%module">MyBusinessService</Setting>
    <Setting Target="Host" Name="%settings">min=111
    mid=333
    max=555</Setting>
  </Item>
  <Item Name="Grongier.PEX.MyCombinedBusinessService" Category="" ClassName="Grongier.PEX.BusinessService" PoolSize="1" Enabled="true" Foreground="false" Comment="" LogTraceEvents="true" Schedule="">
    <Setting Target="Host" Name="%classname">MyCombinedBusinessService</Setting>
    <Setting Target="Host" Name="%classpaths">/irisdev/app/src/python/demo:/usr/irissys/mgr/python/pex</Setting>
    <Setting Target="Host" Name="%module">MyCombinedBusinessService</Setting>
    <Setting Target="Host" Name="%settings">min=111
    mid=333
    max=555</Setting>
  </Item>
</Production>
}

}
