import fetch from 'isomorphic-fetch';
import {createAction} from 'redux-actions';
import request from 'superagent';

import WSConnection from './ws';


const startConnecting = createAction('START_CONNECTING');
const wsConnected = createAction('CONNECTED');

export const connectWS = () => (dispatch, getState) => {
    let {connected} = getState();

    dispatch(startConnecting());

    let ws = new WSConnection('ws://localhost:8000/ws', {
        onmessage: data => dispatch(messageReceived(data)),
        onclose: () => dispatch(wsDisconnected())
    });

    return ws.connect().then(wsConnected);

}


export const wsDisconnected = () => (dispatch, getState) => {

}


export const messageReceived = data => (dispatch, getState) => {

}