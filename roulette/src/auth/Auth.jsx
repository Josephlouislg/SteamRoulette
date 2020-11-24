import React, {useContext} from 'react';

import {Route, Redirect} from "react-router-dom";
import {AuthContext} from "./AuthContext";

const loading = (
  <div className="pt-3 text-center">
    <div className="sk-spinner sk-spinner-pulse"></div>
  </div>
)

const RoutesWithAuth = ({children}) => {
    const { user, isLoading } = useContext(AuthContext);
    if (isLoading) {
        return loading
    }
    if (user) {
        return (
            <Route path='/'>
                {children}
            </Route>
        );
    }
    return <Redirect to='/login' />;
};

export default RoutesWithAuth;