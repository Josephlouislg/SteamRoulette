import React, {useEffect} from 'react'
import {
  CCard,
  CCardBody,
  CCardFooter,
  CCardHeader,
  CCol,
  CFormGroup,
  CInput,
  CLabel,
  CRow
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import {authErrors} from "./bot_constants";
import {WebsocketContext} from "../../../websocket/WebsocketConnector";

const SteamAccountLoginForm = ({onSubmit}) => {
  const [state, setState] = React.useState({username:"", password:""})
  const onFormSubmit = () => {
      const data = {
          username: state.username,
          password: state.password,
          message_type: "bot_registration",
          type: "init"
      };
      onSubmit(data)
  };
  return (
    <>
      <CRow>
        <CCol xs="12" sm="6">
          <CCard>
            <CCardHeader>
              Bot register
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol xs="12">
                  <CFormGroup>
                    <CLabel htmlFor="username">Username</CLabel>
                    <CInput
                      id="username"
                      placeholder="Enter bot username"
                      required
                      value={state.username}
                      onChange={({target}) => setState({...state, username: target.value})}
                    />
                  </CFormGroup>
                </CCol>
              </CRow>
              <CRow>
                <CCol xs="12">
                  <CFormGroup>
                    <CLabel htmlFor="password">Password</CLabel>
                    <CInput
                      id="password"
                      placeholder="********"
                      required
                      value={state.password}
                      type="password"
                      onChange={({target}) => setState({...state, password: target.value})}
                    />
                  </CFormGroup>
                </CCol>
              </CRow>
            </CCardBody>
            <CCardFooter>
                <button className="btn btn-primary btn-sm" type="submit" onClick={onFormSubmit}>
                    <CIcon name="cil-scrubber" />
                    Submit
                </button>
            </CCardFooter>
          </CCard>
        </CCol>
      </CRow>
    </>
  )
}

const BotRegisterForm = () => {
    const [state, setState] = React.useState({formState:null, errorData: null})

    const { subscribe, unsubscribe, sendMessage } = React.useContext(WebsocketContext);

    useEffect(() => {
        const receiveMessage = (msg) => {
          if (msg.message_type !=='bot_registration') {
            return
          }
          console.log(msg);
          setState({...state, formState: msg.error, errorData: msg.error_data})
        };
        subscribe(receiveMessage)
        return () => unsubscribe(receiveMessage)
    }, []);
    const initForm = !state.formState || state.formState == authErrors.invalidPassword
    return (
        <React.Fragment>
            {initForm? <SteamAccountLoginForm onSubmit={sendMessage}/>: null}
        </React.Fragment>
    )
}
export default BotRegisterForm
