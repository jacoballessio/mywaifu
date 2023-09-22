import logo from './logo.svg';
import './App.css';
import ChatBox from './components/ChatBox';
import React from 'react';
import {hostname} from './config.js'
function App() {
  //when the email form is submitted, send the email to jacob.allessio+mywaifuchat@gmail.com
  //email ref
  const emailInputRef = React.useRef(null);
  const formRef = React.useRef(null);
  React.useEffect(() => {
    //get the email form
    const emailForm = document.getElementById('email-form');
    //add an event listener to the form
    emailForm.addEventListener('submit', (e) => {
      //prevent the form from submitting
      console.log('form submitted');
      e.preventDefault();
      //get the email from the form
      const emailInput = emailInputRef.current.value;
      //replace emailForm with a message saying "Sending..."
      formRef.current.innerHTML = '<p class="submit-thank-you">Sending...</p>';
      fetch(hostname+'/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({"email": emailInput})
      })
      .then(response => response.json())
      .then(data => {
        formRef.current.innerHTML = '<p class="submit-thank-you">Thank you for your interest! We will be in touch soon.</p>';
      });
    });
  }, []);


  return (
    <div className="App">
      <header className="App-header">
        <div className="information-section">
          <h1>
            Welcome to MyWaifu.chat
          </h1>
          <p>
          This is an early version of the MyWaifu.chat website. Check out the free demo to the right! You may send up to 15 messages for free.
If you wish to continue chatting after 15 messages you will need to sign up for our private alpha version.
          </p>
          <h1 style={{marginTop: '25%', paddingBottom: '15px', borderBottom: '1px solid #444444', width: '100%'}}>
            Request alpha access
          </h1>
          <p>
            Want to continue chatting? Sign up for our free private alpha!
          </p>
          <form id='email-form' ref={formRef}>
            <input type="text" placeholder="Email" id='email-input' ref={emailInputRef}/>
            <div style={{width: '10px'}}></div>
            <button type='submit'>Request Access</button>
          </form>

        </div>
        <ChatBox />
      </header>
    </div>
  );
}

export default App;
