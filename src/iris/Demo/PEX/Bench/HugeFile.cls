Class PEX.Bench.HugeFile
{

ClassMethod HugeFile(file As %String) As %Status
{
    Set sc = $$$OK
    set tjson = ##class(%Stream.GlobalCharacter).%New()
    d file.%ToJSON(tjson)
    set dyna = {}.%FromJSON(tjson)
    Return sc
}

/// Description
ClassMethod ReadFile() As %Status
{
    Set sc = $$$OK

    #; #; Set tFile = ##class(%File).%New("/tmp/test")
    
    #; Do tFile.Open("RU") 

    #; set str = ""
    #; set len = 1000

    #; set dyna = {}.%FromJSON(tFile)
    #; do dyna.%Set("stream",##class(%Stream.DynamicCharacter).%New("test"),"stream")

    set maxstr=$tr($j("",$$$MaxStringLength)," ","X")
    set maxstr=maxstr_"A"

    set stream = ##class(%Stream.DynamicCharacter).%New()
    do stream.Write(maxstr)
    do stream.Write(maxstr)

    do ##class(PEX.Bench.HugeFile).HugeFile(stream)

    Return sc
}

/// test
ClassMethod test() As %Status
{
    Set sc = $$$OK
    set maxString = $tr($j("",$$$MaxStringLength)," ","X")

    set stream = ##class(%Stream.GlobalCharacter).%New()
    do stream.Write(maxString)
    do stream.Write(maxString)
    do stream.Write("endmax")

    set dyna = {}
    set dyna.maxString = maxString
    set dyna.hugeString = stream
    do dyna.%Set("hugeString", stream,"stream")

    do ##class(PEX.Bench.HugeFile).HugeFile(dyna)

    Return sc
}

ClassMethod MaxString() As %String
{
    quit $tr($j("",$$$MaxStringLength)," ","X")
}

ClassMethod Python2() As %Status [ Language = python ]
{
    import iris
    stream = iris.cls('%Stream.GlobalCharacter')._New()
    stream.Write(iris.cls('PEX.Bench.HugeFile').MaxString())
    stream.Write(iris.cls('PEX.Bench.HugeFile').MaxString())
    iris.cls('PEX.Bench.HugeFile').HugeFile(stream)
}

ClassMethod Python() As %Status [ Language = python ]
{
    file_path = '/irisdev/app/misc/mov.mkv'
    f = open(file_path, 'rb')
    file_content = f.read()
    f.close()
    import iris
    from grongier.pex import BusinessProcess,Message
    bp = BusinessProcess()
    msg = Message()
    msg.bytes = file_content
    request = bp._serialize(msg)
    i = request.find(":")
    dyna = iris.cls('%DynamicObject')._New()
    dyna._Set('stream','request[i+1:]')
    with open('/tmp/test','w') as f:
        f.write(request[i+1:])
    iris.cls('PEX.Bench.HugeFile').HugeFile(dyna)
}

ClassMethod CosReturnError()
{
	q $SYSTEM.Status.Error(101,"5","10","2.7")
}

}
