import React, { useEffect, useRef } from 'react';

const ImageAudioAnimation = ({ frames, timings, audioSrc, onload }) => {
  const canvasRef = useRef(null);
  const firstFrameRef = useRef(null);
  const timeoutIds = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const audio = new Audio(audioSrc);
    let images = [];
    const preloadImages = () => {
      
      return Promise.all(
        frames.map((src) => {
          return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
          });
        })
      );
    };

    preloadImages().then((loadedImages) => {
      //disable first frame
      firstFrameRef.current.style.display = 'none';
      images = loadedImages;

      // Start audio and animation
      

      timings.forEach((timing, index) => {
        console.log(timing);
        const timeoutId = setTimeout(() => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(images[index], 0, 0, canvas.width, canvas.height);
        }, timing);

        timeoutIds.current.push(timeoutId);
      });
      audio.pause();
      audio.play();
      onload();
    });

    return () => {
      // Clear timeouts when component is unmounted
      timeoutIds.current.forEach((id) => clearTimeout(id));
      // Stop audio when component is unmounted
      audio.pause();
    };
  }, [frames, timings, audioSrc, onload]);

  return <><img id="first-frame" className="chat-avatar" src={frames[0]} ref={firstFrameRef}></img><canvas ref={canvasRef} width="640" height="480" className='chat-avatar'></canvas></>;
};

export default ImageAudioAnimation;
