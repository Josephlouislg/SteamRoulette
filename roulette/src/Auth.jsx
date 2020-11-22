import React from 'react';

import {Route, Redirect} from "react-router-dom";

const RoutesWithAuth = ({user, children}) => {
    console.log(children)
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