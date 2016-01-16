import {handleActions} from 'redux-actions';


const rootReducer = handleActions({
    START_CONNECTING: (state, action) => {

    }
}, {
    _wsConnection: null,
    connected: false
});

export default rootReducer;