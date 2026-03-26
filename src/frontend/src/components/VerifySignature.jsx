import React, { useRef, useState, useEffect } from "react";
import SignatureCanvas from "react-signature-canvas";
import "./SignatureCanvas.css";

const VerifySignature = () => {
  const sigCanvas = useRef(null);

  const strokeRef = useRef([]);

  const [userId, setUserId] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // ===============================
  // STROKE CAPTURE
  // ===============================
  useEffect(() => {
    if (!sigCanvas.current) return;

    const canvas = sigCanvas.current.getCanvas();
    let drawing = false;
    let tempStroke = [];

    const getPos = (e) => {
      const rect = canvas.getBoundingClientRect();
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        time: Date.now()
      };
    };

    const start = (e) => {
      drawing = true;
      tempStroke = [getPos(e)];
    };

    const move = (e) => {
      if (!drawing) return;
      tempStroke.push(getPos(e));
    };

    const end = () => {
      if (drawing && tempStroke.length > 0) {
        strokeRef.current.push(tempStroke);
      }
      drawing = false;
      tempStroke = [];
    };

    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    canvas.addEventListener("mouseup", end);
    canvas.addEventListener("mouseleave", end);

    return () => {
      canvas.removeEventListener("mousedown", start);
      canvas.removeEventListener("mousemove", move);
      canvas.removeEventListener("mouseup", end);
      canvas.removeEventListener("mouseleave", end);
    };
  }, []);

  // ===============================
  // VERIFY FUNCTION
  // ===============================
  const verifySignature = async () => {
    const strokes = strokeRef.current;

    if (!userId.trim()) {
      setMessage("Enter User ID");
      return;
    }

    if (strokes.length === 0) {
      setMessage("Draw signature first");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    const image = sigCanvas.current.getCanvas().toDataURL("image/png");
    console.log({
  user_id: userId,
  signature: { image, strokes }
});

    try {
      const response = await fetch("http://127.0.0.1:5000/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          signature: {
            image,
            strokes
          }
        })
      });

      const res = await response.json();
      const data = Array.isArray(res) ? res[0] : res;

      setResult(data);
    } catch (err) {
      console.error(err);
      setMessage("Verification failed");
    } finally {
      setLoading(false);
    }
  };

  // ===============================
  // CLEAR CANVAS
  // ===============================
  const clearCanvas = () => {
    sigCanvas.current.clear();
    strokeRef.current = [];
    setResult(null);
    setMessage("");
  };

  // ===============================
  // UI
  // ===============================
  return (
    <div className="sig-container">
      <h2>Signature Verification</h2>

      {/* USER ID INPUT */}
      <input
        type="text"
        placeholder="Enter User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        className="user-input"
      />

      {/* CANVAS */}
      <SignatureCanvas
  ref={sigCanvas}
  penColor="black"
  backgroundColor="white"   // 🔥 ADD THIS LINE
  canvasProps={{
    width: 500,
    height: 250,
    className: "sig-canvas"
  }}
/>

      {/* BUTTONS */}
      <div className="btn-group">
        <button className="btn clear" onClick={clearCanvas}>
          Clear
        </button>

        <button
          className="btn submit"
          onClick={verifySignature}
          disabled={loading}
        >
          {loading ? "Verifying..." : "Verify Signature"}
        </button>
      </div>

      {/* RESULT */}
      {result && (
        <div className="result">
          <h3>
            {result.verified ? "✅ Genuine Signature" : "❌ Forgery Detected"}

          </h3>

          <p>Score: {result.score}</p>
          <p>Threshold: {result.threshold}</p>
          <p>static score: {result.static_score}</p>
          <p>dynamic score: {result.dynamic_score}</p>
          <p>final score: {result.final_score}</p>
        </div>
      )}

      {/* MESSAGE */}
      {message && <p className="msg info">{message}</p>}
    </div>
  );
};

export default VerifySignature;
