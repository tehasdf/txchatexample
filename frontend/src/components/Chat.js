import React from 'react';
import ReactDOM from 'react-dom';
import {connect} from 'react-redux';

import {sendLine} from '../actions';

const mapStateToProps = state => ({
    lines: state.chat.lines
});

const mapDispatchToProps = {
    sendLine
};


const Chat = ({lines, sendLine}) => (
    <div>
        <ul className="lines">
            {lines.map(line => (
                <li key={line.log_id}><span className="nick">&lt;{line.name}&gt;</span> <span>{line.text}</span></li>
            ))}
        </ul>
        <form onSubmit={evt => {
            evt.preventDefault();
            let line = evt.target.line.value;
            sendLine(line);
            evt.target.line.value = '';
        }}>
            <input
                name="line"
                autoComplete="off"
                type="text"
            />
        </form>
    </div>
);


export default connect(mapStateToProps, mapDispatchToProps)(Chat);
