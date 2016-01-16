import React, {Component} from 'react';
import ReactDOM from 'react-dom';
import {Link} from 'react-router';
import {connect} from 'react-redux';
import {routeActions} from 'redux-simple-router';
import {connectWS} from '../actions';

const mapDispatchToProps = {
    push: routeActions.push,
    connectWS
};


class App extends Component{
    componentDidMount(){
        this.props.connectWS();
    }
    render(){
        return <div className="container">
            <div className="row">
                <div className="col-lg-1">
                    <Link to="/">Home</Link>
                </div>
                <div className="col-lg-1">
                    <Link to="/settings">Settings</Link>
                </div>
                <div className="col-lg-1">
                    <Link to="/chat">Chat</Link>
                </div>
            </div>
            <div className="row">
                <div className="col-lg-12">
                    {this.props.children}
                </div>
            </div>
        </div>
    }
}


export default connect(null, mapDispatchToProps)(App);