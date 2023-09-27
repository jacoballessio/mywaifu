//text that says timing and animated ...

import React from 'react';
import './Typing.css';

const Typing = (props) => {
    const [isTyping, setIsTyping] = React.useState(props.isTyping);
    React.useEffect(() => {
        setIsTyping(props.isTyping);
    }, [props.isTyping]);

    return (
        <>
            {isTyping?<p className='typing'>Typing...</p>:null}
        </>
    );
    }

export default Typing;
