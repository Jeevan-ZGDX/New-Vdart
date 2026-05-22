import React, { useState, useEffect, useRef } from "react";

export default function WebcamView({ isRunning }) {
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);

  useEffect(() => {
    if (isRunning) {
      navigator.mediaDevices
        .getUserMedia({ video: { width: 640, height: 480 } })
        .then((mediaStream) => {
          setStream(mediaStream);
          if (videoRef.current) {
            videoRef.current.srcObject = mediaStream;
          }
        })
        .catch((err) => {
          console.error("Webcam access denied:", err);
        });
    } else {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
        setStream(null);
      }
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [isRunning]);

  return (
    <div className="relative bg-surface rounded-lg overflow-hidden border border-border">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-auto"
        style={{ display: isRunning ? "block" : "none" }}
      />
      <canvas ref={canvasRef} className="absolute top-0 left-0 w-full h-full" />
      {!isRunning && (
        <div className="flex items-center justify-center h-64 text-text-secondary">
          Webcam inactive
        </div>
      )}
    </div>
  );
}
