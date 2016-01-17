import React from 'react';
import ReactDOM from 'react-dom';

import {connect} from 'react-redux';
import {setName} from '../actions';


const mapStateToProps = state => ({
    name: state.chat.name
});


const mapDispatchToProps = {
    setName
};


const Settings = ({name, setName}) => (
    <div>
        <label htmlFor="name-input">Name</label>
        <input
            id="name-input"
            type="text"
            value={name}
            onChange={evt => setName(evt.target.value)}
        />
    </div>
);

export default connect(mapStateToProps, mapDispatchToProps)(Settings)