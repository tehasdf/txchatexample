import {handleActions} from 'redux-actions';
import {routeReducer} from 'redux-simple-router';

const rootReducer = handleActions({
    CONNECTED: (state, action) => ({
        ...state,
        connected: true,
        wsConnection: action.payload
    }),
    NAME_CHANGE: (state, action) => ({
        ...state,
        name: action.payload,
        _originalName: (state._originalName !== null ? state._originalName : state.name)
    }),

    NAME_CHANGE_SUCCESS: (state, action) => ({
        ...state,
        _originalName: null
    }),

    NAME_CHANGE_FAILED: (state, action) => ({
        ...state,
        _originalName: null,
        name: state.name
    }),

    USER_DETAILS_RECEIVED: (state, action) => ({
        ...state,
        name: action.payload.name
    })
}, {
    wsConnection: null,
    connected: false,
    name: null,
    _originalName: null, // backup to revert to, if name change fails
});

export default rootReducer;
