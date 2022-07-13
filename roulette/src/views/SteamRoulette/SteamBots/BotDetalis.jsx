import React, {useEffect, useState} from 'react'

import {
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CModal, CModalBody, CModalFooter, CModalHeader,
  CRow
} from '@coreui/react'
import Page404 from "../../pages/page404/Page404";
import aio from "../../../aio";
import Spinner from "../../Loaders/Spinner";
import {botStatuses, getStatusClass, getStatusTitle} from "./botConstants";



const RemoveGuardModal = ({modal, toggle, onConfirm}) => {
  return (
    <CModal
      show={modal}
      onClose={toggle}
    >
      <CModalHeader closeButton>Remove guard</CModalHeader>
      <CModalBody>
        Are you sure for removing guard?
      </CModalBody>
      <CModalFooter>
        <CButton color="danger" onClick={onConfirm}>Delete guard</CButton>{' '}
        <CButton
          color="primary"
          onClick={toggle}
        >Cancel</CButton>
      </CModalFooter>
    </CModal>
  )
};

const BotDetails = ({match}) => {
  const [state, setState] = useState({
        isLoading: true,
        steamBot: null,
        removeGuardModal: false,
    });
    const botId = match.params.id;

  const toggleRemoveGuard = () => {
    setState((state) => {
      return {...state, removeGuardModal: !state.removeGuardModal}
    })
  }
  const removeGuard = async () => {
    const { data, status } = await aio.delete(`/admin/api/trade-bots/${botId}/guard`);
    await fetchBot()
  }
  const fetchBot = async () => {
    if (!botId) return;
    const { data, status } = await aio.get(`/admin/api/trade-bots/${botId}`);
    if (status === 'ok') {
        setState({
            isLoading: false,
            steamBot: data,
        });
    } else {
        setState({
            isLoading: false,
            steamBot: null,
        });
    }
  };
  useEffect(() => {
    fetchBot();
  }, []);

  if (!botId) {
    return <Page404/>
  }
  if (state.isLoading) {
    return <Spinner/>;
  }
  const hasGuard = state.steamBot.status == botStatuses.active;
  const removeGuardBtn = (
    hasGuard?
    <button className="btn btn-danger" onClick={toggleRemoveGuard}>Remove Guard</button>: null
  )
  const GuardDeleteModal = (
      hasGuard?
      <RemoveGuardModal
        toggle={toggleRemoveGuard}
        modal={state.removeGuardModal}
        onConfirm={removeGuard}
      />: null
  )
  return (
    <React.Fragment>
      <CRow>
        <CCol sm="12">
          <CCard>
            <CCardHeader>
              Bot: {state.steamBot.username}
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol md="2">ID</CCol>
                <CCol md="2">{state.steamBot.bot_id}</CCol>
              </CRow>
              <CRow>
                <CCol md="2">Username</CCol>
                <CCol md="2">{state.steamBot.username}</CCol>
              </CRow>
              <CRow>
                <CCol md="2">Status</CCol>
                <CCol md="2">
                  <div className={getStatusClass(state.steamBot.status)}>
                    {getStatusTitle(state.steamBot.status)}
                  </div>
                </CCol>
              </CRow>
              <CRow>
                <CCol md="2">Steam ID</CCol>
                <CCol md="2">{state.steamBot.steam_id}</CCol>
              </CRow>
              <CRow>
                <CCol md="2">Date Added</CCol>
                <CCol md="2">{state.steamBot.date_created}</CCol>
              </CRow>
              <CRow>
                <CCol md="2">Date modified</CCol>
                <CCol md="2">{state.steamBot.date_modified}</CCol>
              </CRow>
              <CRow>
                <CCol>
                  {removeGuardBtn}
                </CCol>
              </CRow>
              {GuardDeleteModal}
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </React.Fragment>
  )
};

export default BotDetails;