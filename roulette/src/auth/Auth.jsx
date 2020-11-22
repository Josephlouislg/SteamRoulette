import React, {useContext} from 'react';

import {Route, Redirect} from "react-router-dom";
import {AuthContext} from "./AuthContext";

const RoutesWithAuth = ({children}) => {
    const { user } = useContext(AuthContext);
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