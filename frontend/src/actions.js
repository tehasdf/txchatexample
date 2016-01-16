import fetch from 'isomorphic-fetch';
import {createAction} from 'redux-actions';
import request from 'superagent';

import WSConnection from './ws';


const startConnecting = createAction('START_CONNECTING');

export const connectWS = () => (dispatch, getState) => {
    let {connected} = getState();

    dispatch(startConnecting());

    let ws = new WSConnection('ws://localhost:8000/ws');

    return ws.connect();

}