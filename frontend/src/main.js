import React from 'react';
import ReactDOM from 'react-dom';
import {compose, createStore, combineReducers, applyMiddleware} from 'redux';
import {Provider} from 'react-redux';
import {Router, Route, IndexRoute} from 'react-router';
import {createHistory} from 'history';
import {syncHistory, routeReducer} from 'redux-simple-router';
import thunkMiddleware from 'redux-thunk';
import createLogger from 'redux-logger';
import reduceReducers from 'reduce-reducers';


import App from './components/App';
import Settings from './components/Settings';
import Chat from './components/Chat';
import Home from './components/Home';
import rootReducer from './reducers';


const reducer = combineReducers({
    chat: rootReducer,
    routing: routeReducer
});

const history = createHistory();
const reduxRouterMiddleware = syncHistory(history);
const logger = createLogger();

const createStoreWithMiddleware = applyMiddleware(
    reduxRouterMiddleware,
    thunkMiddleware,
    logger
)(createStore);

const store = createStoreWithMiddleware(reducer);

reduxRouterMiddleware.listenForReplays(store);


window.addEventListener('DOMContentLoaded', evt => {
    ReactDOM.render(
      <Provider store={store}>
        <Router history={history}>
          <Route path="/" component={App}>
            <IndexRoute component={Home} />
            <Route path="settings" component={Settings} />
            <Route path="chat" component={Chat} />
          </Route>
        </Router>
      </Provider>,
      document.getElementById('root')
    );
});