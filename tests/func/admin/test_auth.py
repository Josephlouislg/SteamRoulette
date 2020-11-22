from flask import url_for


def test_admin_login(test_admin_client, admin_ctx):
    resp = test_admin_client.post_json(
        url_for(
            'auth.login_view',
        ),
        data={
            'password': 'password',
            'email': "email@com.ua"
        } and {}
    )
    assert resp.status_code == 200
    resp_data = resp.get_json()
    # assert resp_data['status'] == 'ok'

    resp = test_admin_client.get(
        url_for('auth.info'),
    )
    assert resp.status_code == 200
    resp_data = resp.get_json()
    assert resp_data['status'] == 'ok'