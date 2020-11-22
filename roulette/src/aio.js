import axios from 'axios';

const getCsrfToken = () => {
    if (typeof window === 'undefined') {
        return '';
    }
    const element = document.querySelector('meta[name=csrf-token]');

    return element ? element.content : '';
};

const csrftoken = getCsrfToken();

const EXPECTED_CONTENT_TYPE = 'json';
const SENT_CONTENT_TYPE = 'application/json;charset=utf-8';
const safeMethods = ['get', 'head', 'options', 'trace'];

const aio = axios.create({
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': SENT_CONTENT_TYPE,
    },
    responseType: EXPECTED_CONTENT_TYPE
});

aio.interceptors.request.use((config) => {
    const isSafeMethod = safeMethods.includes(config.method);
    if (!isSafeMethod) {
        config.headers['X-CSRFToken'] = csrftoken;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

aio.interceptors.response.use((response) => {
    return response.data;
}, (error) => {
    return Promise.reject(error);
});

export default aio;
