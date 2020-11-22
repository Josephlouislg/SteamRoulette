import React, {useContext, useState} from 'react'
import { Redirect } from 'react-router-dom'
import {
  CCard,
  CCardBody,
  CCardGroup,
  CCol,
  CContainer,
  CForm,
  CInputGroup,
  CInputGroupPrepend,
  CInputGroupText,
  CRow
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import aio from "../../../aio";
import {AuthContext} from "../../../auth/AuthContext";

const Login = () => {
  const [state, setState] = useState({email:'', password: ''});
  const { user, setUser } = useContext(AuthContext);

  if (user) {
    return <Redirect to='/' />
  }
  const DoLogin = async () => {
    const result = await aio.post(
        '/admin/api/auth/login',
        {email: state.email, password: state.password}
    );
    if (result.status === 'ok') {
      setUser(result.data.admin)
    }
  };
  return (
    <div className="c-app c-default-layout flex-row align-items-center">
      <CContainer>
        <CRow className="justify-content-center">
          <CCol md="8">
            <CCardGroup>
              <CCard className="p-8">
                <CCardBody>
                  <CForm>
                    <h1>Login</h1>
                    <p className="text-muted">Sign In to your account</p>
                    <CInputGroup className="mb-3">
                      <CInputGroupPrepend>
                        <CInputGroupText>
                          <CIcon name="cil-user" />
                        </CInputGroupText>
                      </CInputGroupPrepend>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Email"
                        name='email'
                        value={state.email}
                        onChange={({target}) => setState({...state, email: target.value})}
                      />
                    </CInputGroup>
                    <CInputGroup className="mb-4">
                      <CInputGroupPrepend>
                        <CInputGroupText>
                          <CIcon name="cil-lock-locked" />
                        </CInputGroupText>
                      </CInputGroupPrepend>
                      <input
                        type="password"
                        className="form-control"
                        placeholder="Password"
                        id='password'
                        value={state.password}
                        onChange={({target}) => setState({...state, password: target.value})}
                      />
                    </CInputGroup>
                    <CRow>
                      <CCol xs="6">
                        <button
                            type='button'
                            className="px-4 btn-primary btn"
                            onClick={DoLogin}
                        >
                          Login
                        </button>
                      </CCol>
                    </CRow>
                  </CForm>
                </CCardBody>
              </CCard>
            </CCardGroup>
          </CCol>
        </CRow>
      </CContainer>
    </div>
  )
}

export default Login
