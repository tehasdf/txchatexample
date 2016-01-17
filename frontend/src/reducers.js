import {handleActions} from 'redux-actions';
import {routeReducer} from 'redux-simple-router';

const rootReducer = handleActions({
    CONNECTED: (state, action) => ({
        ...state,
        connected: true,
        _wsConnection: action.payload
    })
}, {
    _wsConnection: null,
    connected: false
});

export default rootReducer;
