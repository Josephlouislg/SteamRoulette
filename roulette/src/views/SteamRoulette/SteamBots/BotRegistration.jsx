import React, {useEffect} from 'react'
import {
    CCard,
    CCardBody,
    CCardFooter,
    CCardHeader,
    CCol,
    CFormGroup, CImg,
    CInput,
    CLabel,
    CRow
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import {authErrors} from "./botConstants";
import {WebsocketContext} from "../../../websocket/WebsocketConnector";

const SteamAccountLoginForm = ({onSubmit}) => {
  const [state, setState] = React.useState({username:"", password:"", disable: false})
  const onFormSubmit = () => {
      const data = {
          username: state.username,
          password: state.password,
          message_type: "bot_registration",
          type: "init"
      };
      setState({...state, disable: true})
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
                <button className="btn btn-primary btn-sm" disabled={state.disable} type="submit" onClick={onFormSubmit}>
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

const AuthCodeForm = ({onSubmit, errorData}) => {
    const [state, setState] = React.useState({code: "", disable: false})
    const { msg: msg, captcha_url: captchaUrl } = errorData;
    const onFormSubmit = () => {
      const data = {
          code: state.code,
          message_type: "bot_registration",
          type: "auth"
      };
      setState({...state, disable: false})
      onSubmit(data)
    };
    const captcha = captchaUrl ? <CImg src={captchaUrl} /> : null
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
                    <CLabel htmlFor="code">{msg}</CLabel>
                    <CInput
                      id="code"
                      placeholder={msg}
                      required
                      value={state.code}
                      onChange={({target}) => setState({...state, code: target.value})}
                    />
                  </CFormGroup>
                </CCol>
                {captcha}
              </CRow>
            </CCardBody>
            <CCardFooter>
                <button className="btn btn-primary btn-sm" disabled={state.disable} type="submit" onClick={onFormSubmit}>
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
          setState({...state, formState: msg.error, errorData: msg.error_data})
        };
        subscribe(receiveMessage)
        return () => unsubscribe(receiveMessage)
    }, []);
    const initForm = !state.formState || state.formState == authErrors.invalidPassword
    return (
        <React.Fragment>
            {initForm? <SteamAccountLoginForm onSubmit={sendMessage}/>: null}
            {!initForm? <AuthCodeForm onSubmit={sendMessage} errorData={state.errorData}/>: null}
        </React.Fragment>
    )
}
export default BotRegisterForm
