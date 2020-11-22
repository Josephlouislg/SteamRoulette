import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useHistory } from 'react-router-dom';


import aio from "../aio";


export const AuthContext = React.createContext();
const { Provider } = AuthContext;


export const AuthProvider = ({ children }) => {
    const [state, setState] = useState({
        isLoading: true,
        user: null,
    });
    const histrory = useHistory();

    const setUser = useCallback((user) => {
        setState((prevState) => ({ ...prevState, user }));
    }, []);

    const onLogout = useCallback(async () => {
        setState((prevState) => ({ ...prevState, isLoading: true }));

        const { status } = await aio.post('admin/api/auth/logout');

        if (status === 'ok') {
            setState({ isLoading: false, user: null });
        }
    }, []);

    useEffect(() => {
        const fetchUser = async () => {
            const { data, status } = await aio.get('/admin/api/auth/info');
            if (status === 'ok') {
                setState({
                    isLoading: false,
                    user: data.admin,
                });
            } else {
                setState({
                    isLoading: false,
                    user: null,
                });
                histrory.replace('/login');
            }
        };

        fetchUser();
    }, []);

    const contextValue = useMemo(() => {
        return {
            ...state,
            setUser,
            onLogout,
        };
    }, [state]);

    return (
        <Provider value={contextValue}>
            {children}
        </Provider>
    );
};
