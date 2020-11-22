import React, { Component } from 'react';
import { HashRouter, Route, Switch } from 'react-router-dom';
import './scss/style.scss';
import RoutesWithAuth from "./auth/Auth";
import Login from "./views/pages/login/Login";
import {AuthProvider} from "./auth/AuthContext";
import {WebSocketProvider} from "./websocket/WebsocketConnector";

const loading = (
  <div className="pt-3 text-center">
    <div className="sk-spinner sk-spinner-pulse"></div>
  </div>
)

// Containers
const TheLayout = React.lazy(() => import('./containers/TheLayout'));

// Pages
const Register = React.lazy(() => import('./views/pages/register/Register'));
const Page404 = React.lazy(() => import('./views/pages/page404/Page404'));
const Page500 = React.lazy(() => import('./views/pages/page500/Page500'));


class App extends Component {

  render() {
    return (
      <HashRouter>
          <React.Suspense fallback={loading}>
            <AuthProvider>
              <WebSocketProvider>
                <Switch>
                  <Route exact path="/login" name="Login Page" render={props => <Login {...props}/>} />
                  <RoutesWithAuth>
                    <React.Fragment>
                      <Route exact path="/register" name="Register Page" render={props => <Register {...props}/>} />
                      <Route exact path="/404" name="Page 404" render={props => <Page404 {...props}/>} />
                      <Route exact path="/500" name="Page 500" render={props => <Page500 {...props}/>} />
                      <Route path="/" name="Home" render={props => <TheLayout {...props}/>} />
                    </React.Fragment>
                  </RoutesWithAuth>
                </Switch>
              </WebSocketProvider>
            </AuthProvider>
          </React.Suspense>
      </HashRouter>
    );
  }
}

export default App;
