import React, { useState } from 'react';
import './CreditCircle.css';
const CreditCircle = (props) => {
  const [credits, setCredits] = useState(props.credits);

  //make sure credits gets updated when props.credits changes
  React.useEffect(() => {
    setCredits(props.credits);
  }, [props.credits]);
  
  return (
    <div style={{ textAlign: 'center', alignSelf: 'flex-end'}} id={props.id}>
      
      <div style={{position: 'relative', fontSize: "12px", borderBottom: '1px solid rgba(255,255,255,0.1)', padding: '5px', marginBottom: '5px', color: '#CDCED6'}}>Credits</div>
      <div 
        style={{ 
          width: '40px', // Both where 50px, testing smaller circle for Desktop
          height: '40px', 
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          margin: '0 auto',
        }}
        className='credit-circle'
      >
        {credits}
      </div>
      {props.addable?<button className='credit-button'>+</button>:null}
    </div>
  );
};

export default CreditCircle;
