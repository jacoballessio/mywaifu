//chat box functional component
import React from 'react';
import './ChatBox.css';
import MBP from '../assets/imgs/MBP.png';
import CreditCircle from './CreditCircle';
import ImageAudioAnimation from './ImageAudioAnimation';

import {hostname} from '../config.js'
const delayAmount = 0.01;

function ChatBox(props) {
    //initialize messages to props.messages
    //get messages from local storage
    const startingCredits = 15;
    const [messages, setMessages] = React.useState(JSON.parse(localStorage.getItem('messages')) || []);
    const chatBoxBodyRef = React.useRef(null);
    const [credits, setCredits] = React.useState(localStorage.getItem('credits') || startingCredits);

    //on messages re-render, scroll to the bottom
    React.useEffect(() => {
        chatBoxBodyRef.current.scrollTop = chatBoxBodyRef.current.scrollHeight;
        //we should keep track of the messages in local storage
        //the number of user messages in local storage will be how many credits the user has used.
        //the user should start off with 5 credits
        //when the user runs out of credits, they should be prompted to sign up for the private alpha
        localStorage.setItem('messages', JSON.stringify(messages));
        //set credits to the starting credits- the number of user messages
        let credits = startingCredits - messages.filter(message => message.type === 'user').length;
        if (credits < 0) {
            credits = 0;
        }
        setCredits(credits);
        localStorage.setItem('credits', credits);

    }, [messages]);

    const [avatarAnimation, setAvatarAnimation] = React.useState(<img src={MBP} alt="MBP" className='chat-avatar'/>);
    if (props.messages) {
        setMessages(props.messages);
    }
    const sendMessage = () => {
       
        //check if the user has any credits left
        if (credits <= 0) {
            //if not, prompt them to sign up for the private alpha
            alert('You have run out of credits. Please sign up for the private alpha to continue chatting.');
            return;
        }

        //get the message from the input box
        const message = document.getElementById('message-input').value;
        //clear the input box
        let messageElement = {message: message, type: 'user'};
        let typingElement = {message: 'typing...', type: 'AI'};
        setMessages(prevMessages => [...prevMessages, messageElement, typingElement])
         //if waiting on a response, don't send another message
        try{
            console.log(messages[messages.length-1])
            if (messages[messages.length-1].type === 'user') {
                return;
            }
        } catch (e) {
            //messages is empty
        }
        document.getElementById('message-input').value = '';
        //send the message to the server
        fetch(hostname+'/llm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({"text": [...messages, messageElement]})
        })
        .then(response => response.json())
        .then(data => {
            //add the message and response to the chat box
            //as plain text
            //remove typing element
            console.log(data);
            console.log(data.llm_response);
            let resElement = {message: data.llm_response, type: 'ai'};
            //begin animation. Frames and timings are in data.phoneme_mappings. data.phoneme_mappings is a tuple where the first element is the frame and second/third are start/end times
            let frames = [];
            let timings = [];
            console.log(data.phoneme_mappings);
            for (let i = 0; i < data.phoneme_mappings.length; i++) {
                frames.push(hostname+'/'+data.phoneme_mappings[i][0]);
                timings.push(data.phoneme_mappings[i][1]*1000);
            }
            //stop all previous audio
            let audios = document.getElementsByTagName('audio');
            for (let i = 0; i < audios.length; i++) {
                audios[i].pause();
            }
            setAvatarAnimation(<ImageAudioAnimation frames={frames} timings={timings} audioSrc={hostname+'/'+data.tts_audio} 
                onload={function(){
                    
                    setMessages(prevMessages => prevMessages.slice(0, prevMessages.length-1));
                    
                    setMessages(prevMessages => [...prevMessages, resElement])
                    
                }}
            />);
            
        });
    };
    return (
            
        <div className="chatBox">
            <div className="chatBoxHeader">
                <div className="chatBoxHeaderContent">
                    <div className="chatBoxHeaderName">
                        {props.name}
                    </div>
                    <div className="chatBoxHeaderStatus">
                        {props.status}
                    </div>
                    <CreditCircle credits={credits}/>
                </div>
            </div>
            <div className="chatBoxBody" ref={chatBoxBodyRef} id="chatBoxBody">
                {messages.map((message, index) => {
                                let delay = 0;
                                if (message.type === 'user') {
                                    return (
                                        <div className="chatBoxBodyMessage user-message" key={index}>
                                            {/*split each character into a span*/}
                                            {Array.from(message.message).map((char, index) => {
                                                
                                                let delayAmount = Math.random()*0.1;
                                                delay+=delayAmount;
                                                if (char === ' ') {
                                                    char = '\u00A0';
                                                }
                                                return (
                                                    <span key={index} style={{animationDelay:delay+'s'}}>{char}</span>
                                                )
                                            })}
                                        </div>
                                    )
                                }
                                else {
                                    return (
                                        <div className="chatBoxBodyMessage ai-message" key={index}>
                                            {/*split each character into a span*/}
                                            {/*remove leading and trailing whitespace*/}
                                            {Array.from(message.message.trim()).map((char, index) => {
                                                
                                                let delayAmount = Math.random()*0.1;
                                                delay+=delayAmount;
                                                if (char === ' ') {
                                                    char = '\u00A0';
                                                }
                                                return (
                                                    <span key={index} style={{animationDelay:delay+'s'}}>{char}</span>
                                                )
                                            })}

                                        </div>
                                    )
                                }
                            })}
            </div>
            <div className="chatBoxFooter">
                
                {/*<img src={MBP} alt="MBP" className='chat-avatar'/>*/}
                <div className="chat-avatar">
                    {avatarAnimation}
                </div>
                <div className="chatBoxFooterContent">
                    <input type="text" id="message-input" className="chatBoxFooterMessage" placeholder="Type a message" onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                                sendMessage();
                            }
                        }}/>
                    <button id="send-button" onClick={sendMessage}>Send</button>
                </div>
            </div>
        </div>
    );
}

export default ChatBox;