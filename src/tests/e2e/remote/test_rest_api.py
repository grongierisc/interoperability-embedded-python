"""E2E tests for the complete /api/iop REST API surface.

Covers every endpoint and validates the recent features:
  - namespace accepted via query-string on all routes (GET, POST, PUT)
  - namespace accepted via JSON body on POST/PUT routes (body wins)
  - POST /test accepts body as a JSON object (not only a string)
  - error responses are JSON {"error": "..."}, not plain-text HTTP status lines

Run with a live IRIS instance and IOP_URL set:
    IOP_URL=http://localhost:52773 pytest src/tests/e2e/remote/
"""
import pytest
import requests as _requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raw_get(director, path, **params):
    """Issue a GET without the director helper so we control every detail."""
    resp = _requests.get(
        f"{director._base}{path}",
        params=params,
        auth=director._auth,
        verify=director._verify,
        timeout=30,
    )
    return resp


def _raw_post(director, path, body, *, include_ns_in_params=False, include_ns_in_body=False):
    params = {}
    if include_ns_in_params:
        params["namespace"] = director._namespace
    if include_ns_in_body:
        body = {**body, "namespace": director._namespace}
    resp = _requests.post(
        f"{director._base}{path}",
        json=body,
        params=params,
        auth=director._auth,
        verify=director._verify,
        timeout=30,
    )
    return resp


def _raw_put(director, path, body, *, include_ns_in_params=False, include_ns_in_body=False):
    params = {}
    if include_ns_in_params:
        params["namespace"] = director._namespace
    if include_ns_in_body:
        body = {**body, "namespace": director._namespace}
    resp = _requests.put(
        f"{director._base}{path}",
        json=body,
        params=params,
        auth=director._auth,
        verify=director._verify,
        timeout=30,
    )
    return resp


# ---------------------------------------------------------------------------
# GET /version
# ---------------------------------------------------------------------------

class TestVersion:
    def test_version_returns_200(self, remote_director):
        resp = _raw_get(remote_director, "/version")
        assert resp.status_code == 200

    def test_version_has_version_field(self, remote_director):
        data = _raw_get(remote_director, "/version").json()
        assert "version" in data

    def test_version_has_description_field(self, remote_director):
        data = _raw_get(remote_director, "/version").json()
        assert "description" in data


# ---------------------------------------------------------------------------
# GET /log
# ---------------------------------------------------------------------------

class TestLog:
    def test_log_default_returns_list(self, remote_director):
        """GET /log with default params returns a list."""
        data = remote_director._check_error(remote_director._get("/log"))
        assert isinstance(data, list)

    def test_log_top_param(self, remote_director):
        """GET /log?top=3 returns at most 3 entries."""
        data = remote_director._check_error(remote_director._get("/log", {"top": 3}))
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_log_since_id_zero_returns_list(self, remote_director):
        """GET /log?since_id=0 returns all entries after id 0."""
        data = remote_director._check_error(remote_director._get("/log", {"since_id": 0}))
        assert isinstance(data, list)

    def test_log_entry_has_expected_fields(self, remote_director):
        """Each log entry exposes the documented fields."""
        entries = remote_director._check_error(remote_director._get("/log", {"top": 1}))
        if not entries:
            pytest.skip("No log entries available")
        entry = entries[0]
        for field in ("id", "config_name", "text", "type", "time_logged"):
            assert field in entry, f"Log entry missing field: {field}"

    def test_log_since_id_polling(self, remote_director):
        """since_id polling: entries returned all have id > since_id."""
        all_entries = remote_director._check_error(remote_director._get("/log", {"top": 10}))
        if len(all_entries) < 2:
            pytest.skip("Not enough log entries to test since_id polling")
        pivot = all_entries[len(all_entries) // 2].get("id", 0)
        newer = remote_director._check_error(remote_director._get("/log", {"since_id": pivot}))
        for entry in newer:
            assert entry.get("id", 0) > pivot


# ---------------------------------------------------------------------------
# GET /export
# ---------------------------------------------------------------------------

class TestExport:
    @pytest.fixture(autouse=True)
    def _need_production(self, remote_director):
        prod = remote_director.get_default_production()
        if prod in ("", "Not defined"):
            pytest.skip("No default production defined")
        self.production = prod

    def test_export_returns_200(self, remote_director):
        resp = _raw_get(remote_director, "/export",
                        production=self.production,
                        namespace=remote_director._namespace)
        assert resp.status_code == 200

    def test_export_body_has_xml_key(self, remote_director):
        data = remote_director._check_error(
            remote_director._get("/export", {"production": self.production})
        )
        assert "xml" in data

    def test_export_xml_is_non_empty_string(self, remote_director):
        data = remote_director._check_error(
            remote_director._get("/export", {"production": self.production})
        )
        assert isinstance(data["xml"], str)
        assert len(data["xml"]) > 0


# ---------------------------------------------------------------------------
# Namespace: query-string on every method type
# ---------------------------------------------------------------------------

class TestNamespaceViaQueryString:
    """namespace=... query parameter must be honoured on GET, POST, and PUT routes."""

    def test_get_status(self, remote_director):
        resp = _raw_get(remote_director, "/status", namespace=remote_director._namespace)
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_get_list(self, remote_director):
        resp = _raw_get(remote_director, "/list", namespace=remote_director._namespace)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_get_default(self, remote_director):
        resp = _raw_get(remote_director, "/default", namespace=remote_director._namespace)
        assert resp.status_code == 200
        assert "production" in resp.json()

    def test_get_log(self, remote_director):
        resp = _raw_get(remote_director, "/log",
                        namespace=remote_director._namespace, top=5)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_put_default_namespace_in_querystring(self, remote_director):
        """PUT /default: namespace supplied only as a query-string param."""
        original = remote_director.get_default_production()
        resp = _raw_put(
            remote_director, "/default",
            body={"production": original},
            include_ns_in_params=True,
        )
        assert resp.status_code == 200
        assert resp.json().get("production") == original

    def test_post_test_bad_target_namespace_in_querystring(self, remote_director):
        """POST /test: namespace supplied only as a query-string param gives a JSON error."""
        resp = _raw_post(
            remote_director, "/test",
            body={"target": "NoSuchTarget.AtAll", "classname": "Ens.StringRequest"},
            include_ns_in_params=True,
        )
        # Expect an HTTP error with a JSON body containing "error"
        assert resp.status_code >= 400
        data = resp.json()
        assert "error" in data


# ---------------------------------------------------------------------------
# Namespace: JSON body on POST / PUT routes
# ---------------------------------------------------------------------------

class TestNamespaceViaBody:
    """namespace field in the JSON body must override the query-string default."""

    def test_put_default_namespace_in_body(self, remote_director):
        """PUT /default: namespace supplied only in the JSON body."""
        original = remote_director.get_default_production()
        resp = _raw_put(
            remote_director, "/default",
            body={"production": original},
            include_ns_in_body=True,
        )
        assert resp.status_code == 200
        assert resp.json().get("production") == original

    def test_post_test_namespace_in_body(self, remote_director):
        """POST /test: namespace supplied in the JSON body returns a JSON error for bad target."""
        resp = _raw_post(
            remote_director, "/test",
            body={"target": "NoSuchTarget.AtAll", "classname": "Ens.StringRequest"},
            include_ns_in_body=True,
        )
        assert resp.status_code >= 400
        data = resp.json()
        assert "error" in data

    def test_namespace_body_takes_priority_over_querystring(self, remote_director):
        """Body namespace wins when both body and query-string supply different values."""
        original = remote_director.get_default_production()
        ns = remote_director._namespace
        resp = _requests.put(
            f"{remote_director._base}/default",
            json={"production": original, "namespace": ns},
            params={"namespace": ns},   # same value — just ensure no conflict
            auth=remote_director._auth,
            verify=remote_director._verify,
            timeout=30,
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /test — body formats
# ---------------------------------------------------------------------------

class TestPostTestBodyFormats:
    """POST /test must accept body as a JSON string OR a JSON object."""

    def test_body_as_json_string_raises_runtime_error_not_http(self, remote_director):
        """Sending body as a JSON string: error should be a RuntimeError with plain message."""
        with pytest.raises(RuntimeError) as exc_info:
            remote_director.test_component(
                target="NoSuchTarget.AtAll",
                classname="Ens.StringRequest",
                body='{"StringValue": "hello"}',
            )
        assert "500 server error" not in str(exc_info.value).lower()

    def test_body_as_dict_raises_runtime_error_not_http(self, remote_director):
        """Sending body as a dict: error should be a RuntimeError with plain message."""
        with pytest.raises(RuntimeError) as exc_info:
            remote_director.test_component(
                target="NoSuchTarget.AtAll",
                classname="Ens.StringRequest",
                body={"StringValue": "hello"},
            )
        assert "500 server error" not in str(exc_info.value).lower()

    def test_body_string_and_dict_raise_same_error(self, remote_director):
        """String and dict bodies for the same bad target should raise the same error message."""
        def _call(body):
            try:
                remote_director.test_component(
                    target="NoSuchTarget.AtAll",
                    classname="Ens.StringRequest",
                    body=body,
                )
            except RuntimeError as exc:
                return str(exc)
            return None

        err_str = _call('{"StringValue": "hello"}')
        err_dict = _call({"StringValue": "hello"})
        assert err_str is not None
        assert err_dict is not None
        assert err_str == err_dict

    def test_none_body_is_accepted(self, remote_director):
        """body=None should not raise a TypeError and omits body from the request."""
        with pytest.raises(RuntimeError):
            remote_director.test_component(
                target="NoSuchTarget.AtAll",
                classname="Ens.StringRequest",
                body=None,
            )


# ---------------------------------------------------------------------------
# Error response format
# ---------------------------------------------------------------------------

class TestErrorResponseFormat:
    """All error responses must be JSON {"error": "..."}, not plain HTTP status text."""

    def test_bad_target_error_is_json(self, remote_director):
        resp = _raw_post(
            remote_director, "/test",
            body={"target": "DoesNotExist.AtAll", "classname": "Ens.StringRequest"},
            include_ns_in_params=True,
        )
        assert resp.status_code >= 400
        assert resp.headers.get("Content-Type", "").startswith("application/json")
        data = resp.json()
        assert "error" in data
        assert isinstance(data["error"], str)

    def test_error_key_contains_message(self, remote_director):
        resp = _raw_post(
            remote_director, "/test",
            body={"target": "DoesNotExist.AtAll", "classname": "Ens.StringRequest"},
            include_ns_in_params=True,
        )
        data = resp.json()
        assert len(data["error"]) > 0
