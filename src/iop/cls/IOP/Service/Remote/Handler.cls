Class IOP.Service.Remote.Handler Extends %CSP.REST
{

Parameter CHARSET = "utf-8";

Parameter CONVERTINPUTSTREAM = 1;

Parameter CONTENTTYPE = "application/json";

/// This parameter influences the CORS support. The default is an empty string meaning 'not specified'.
/// If set to true (1) then CORS processing is ON. If set to false (0) then CORS processing is OFF.
/// If left unset "" then the decision to process CORS is delegated to the setting on the URL map route.
Parameter HandleCorsRequest = 1;

Parameter UseSession As Integer = 0;

/// Ignore any writes done directly by the REST method.
Parameter IgnoreWrites = 0;

XData UrlMap [ XMLNamespace = "http://www.intersystems.com/urlmap" ]
{
<Routes>
<!-- Iop Management -->
<Map Prefix="/v1" Forward="IOP.Service.Remote.Rest.v1"/>
<!-- make the default forward to the highest current version of the API -->
<Map Prefix="/*" Forward="IOP.Service.Remote.Rest.v1"/>
</Routes>
}

}
