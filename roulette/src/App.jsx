import React, { Component } from 'react';
import { HashRouter, Route, Switch } from 'react-router-dom';
import './scss/style.scss';
import aio from "./aio";
import RoutesWithAuth from "./Auth";
import Login from "./views/pages/login/Login";

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
  async fetchUser() {
    const { data } = await aio.get('/admin/api/auth/info');
    this.setState({"user": data})  // TODO: Set user to context
  }
  componentWillMount() {
    this.setState({user: null})
    this.fetchUser();
  }

  render() {
    const loginProps = {user: this.state.user, onLogin: this.fetchUser.bind(this)}
    return (
      <HashRouter>
          <React.Suspense fallback={loading}>
            <Switch>
              <Route exact path="/login" name="Login Page" user={this.state.user} render={props => <Login {...{...props, ...loginProps}}/>} />
              <RoutesWithAuth user={this.state.user}>
                <React.Fragment>
                  <Route exact path="/register" name="Register Page" render={props => <Register {...props}/>} />
                  <Route exact path="/404" name="Page 404" render={props => <Page404 {...props}/>} />
                  <Route exact path="/500" name="Page 500" render={props => <Page500 {...props}/>} />
                  <Route path="/" name="Home" render={props => <TheLayout {...props}/>} />
                </React.Fragment>
              </RoutesWithAuth>
            </Switch>
          </React.Suspense>
      </HashRouter>
    );
  }
}

export default App;
