import pytest
import sqlalchemy as sa

from SteamRoulette.service.db import session


# @pytest.yield_fixture
# def db_session(db_engine):
#     #  taken from SA docs: http://bit.ly/1Q6Dv3p
#     conn = db_engine.connect()
#     trans = conn.begin()
#     session.remove()
#     session.configure(bind=conn, autoflush=True, autocommit=False)
#
#     session.begin_nested()
#
#     @sa.event.listens_for(session, 'after_transaction_end')
#     def restart_savepoint(sess, transaction):
#         if transaction.nested and not transaction._parent.nested:
#             sess.expire_all()
#             sess.begin_nested()
#
#     yield session
#
#     session.remove()
#     session.close()
#     trans.rollback()
#     conn.close()
