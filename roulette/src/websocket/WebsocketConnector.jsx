import React, { useEffect, useState, useCallback, useMemo } from 'react';


export const WebsocketContext = React.createContext();
const { Provider } = WebsocketContext;

let ws = null;
let subscribers = [];

export const WebSocketProvider = ({ children }) => {
    const [state, setState] = useState({
        connectInterval: null
    });

    const sendMessage = useCallback((msg) => {
        ws.send(JSON.stringify(msg));
    }, []);

    let timeout = 10000;


    const subscribe = (observer) => {
        console.log(subscribers)
        subscribers = [...subscribers, observer]
    };

    const unsubscribe = (observer) => {
        const removeIndex = subscribers.findIndex(obs => observer === obs);
        if (removeIndex !== -1) {
          subscribers = subscribers.slice(removeIndex, 1);
        }
    };

    const notify = useCallback((msg) => {
      if (subscribers.length > 0) {
          subscribers.forEach(observer => observer(msg));
      }
    }, [])

    const getWSUrl = () => {
        const loc = window.location;
        let schema = "ws:"
        if (loc.protocol === "https:") {
            schema = "wss:";
        }
        const wsUrl = schema + "//" + loc.host + "/admin/api/bots/bot_register";
        return wsUrl;
    }

    const check = useCallback(() => {
        // const { ws } = state;
        if (!ws || ws.readyState === WebSocket.CLOSED) connect(); //check if websocket instance is closed, if so call `connect` function.
    }, []);

    const connect = useCallback(() => {
        const url = getWSUrl();
        ws = new WebSocket(url);
        ws.onopen = () => {
            setState({...state, "ws": ws})
        };
        ws.onclose = e => {
            setState({...state, connectInterval: setTimeout(check, Math.min(10000, timeout))})
        };
        ws.onerror = err => {
            console.error(
                "Socket encountered error: ",
                err.message,
                "Closing socket"
            );

            ws.close();
        };
        ws.onmessage =  ({data}) => {
            const msg = JSON.parse(data);
            notify(msg)
        }
    }, [state.ws]);

    useEffect(() => {
        connect();
    }, []);

    const contextValue = useMemo(() => {
        return {
            ...state,
            sendMessage,
            subscribe,
            unsubscribe,
        };
    }, [state, sendMessage, subscribe, unsubscribe]);

    return (
        <Provider value={contextValue}>
            {children}
        </Provider>
    );
};
