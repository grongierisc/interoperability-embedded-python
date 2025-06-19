/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.Generator.Message.StartPickle Extends IOP.PickleMessage [ ClassType = persistent, Inheritance = right, ProcedureBlock ]
{

Parameter DOMAIN = "Generator";

Storage Default
{
<Type>%Storage.Persistent</Type>
}

}
