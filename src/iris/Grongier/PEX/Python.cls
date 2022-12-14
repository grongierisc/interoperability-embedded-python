/// Description
Class Grongier.PEX.Python
{

/// Set classPath
ClassMethod SetClassPath(classPath As %String) As %Status [ Language = python ]
{
import sys
return sys.path.append(classPath)
}

/// GetInstanceFromModuleClassName
ClassMethod GetInstanceFromModuleClassName(modulename, classname) As %SYS.Python [ Language = python ]
{
import builtins
import importlib
module = importlib.import_module(modulename)
return getattr(module, classname)()
}

/// Lenght of python list
ClassMethod Len(pList) [ Language = python ]
{
return len(pList)
}

}
