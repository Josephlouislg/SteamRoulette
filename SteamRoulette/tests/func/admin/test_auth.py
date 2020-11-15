from flask import url_for


def test_admin_login(test_admin_client, admin_ctx):
    resp = test_admin_client.post(
        url_for(
            'auth.login_view',
        )
    )
    assert resp.status_code == 200
