
export default class WSConnection {
    constructor(url, callbacks){
        this._url = url;
        this._conn = null;
        this._messageCallback = callbacks.onmessage;
        this._closeCallback = callbacks.onclose;

    }

    connect(){
        this._conn = new WebSocket(this._url);
        this._conn.onopen = this.onopen.bind(this);
        this._conn.onmessage = this.onmessage.bind(this);
        this._conn.onclose = this.onclose.bind(this);

        return new Promise((resolve, reject) => {
            this._connected = resolve;
        });

    }

    onopen(){
        this._connected(this);
    }

    onmessage(evt){
        let data = JSON.parse(evt.data);
        this._messageCallback(data);
    }

    onclose(){

    }

}
