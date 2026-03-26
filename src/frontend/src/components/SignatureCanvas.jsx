import React, { useRef, useState, useEffect } from "react";
import SignatureCanvas from "react-signature-canvas";
import "./SignatureCanvas.css";

const TOTAL_SIGS = 5;

const RegisterSignature = () => {
  const sigCanvas = useRef(null);

  // 🔥 REAL STORAGE (NOT STATE)
  const signatureStrokesRef = useRef([]);

  const [savedSignatures, setSavedSignatures] = useState([]);
  const [message, setMessage] = useState("");
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(false);

  // ===============================
  // STROKE CAPTURE (REF BASED)
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
        signatureStrokesRef.current.push(tempStroke);
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
  // SAVE ONE SIGNATURE (DEBUG)
  // ===============================
  const saveOneSignature = () => {
    const strokes = signatureStrokesRef.current;

    console.log(`========== SIGNATURE ${savedSignatures.length + 1} ==========`);
    strokes.forEach((stroke, i) => {
      console.log(`Stroke ${i + 1}`);
      stroke.forEach((p, j) => {
        console.log(
          `Point ${j + 1}: x=${p.x}, y=${p.y}, time=${p.time}`
        );
      });
    });
    console.log("====================================");

    if (strokes.length === 0) {
      setMessage("Please draw a signature first.");
      return;
    }

    const image = sigCanvas.current
      .getCanvas()
      .toDataURL("image/png");

    setSavedSignatures((prev) => [
      ...prev,
      {
        image,
        strokes: JSON.parse(JSON.stringify(strokes))
      }
    ]);

    // 🔥 HARD RESET
    sigCanvas.current.clear();
    signatureStrokesRef.current = [];

    setMessage(`Signature ${savedSignatures.length + 1} saved.`);
  };

  // ===============================
  // SUBMIT ALL
  // ===============================
  const submitRegistration = async () => {
    if (savedSignatures.length !== TOTAL_SIGS) {
      setMessage("Please save all 5 signatures.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ signatures: savedSignatures })
      });

      const result = await response.json();

// ✅ handle Flask tuple response
const data = Array.isArray(result) ? result[0] : result;

setUserId(data.user_id);
setMessage("Registration successful. Save your User ID.");

    } catch (err) {
      console.error(err);
      setMessage("Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  // ===============================
  // UI
  // ===============================
  return (
    <div className="sig-container">
      <h2>Signature Registration</h2>

      {!userId && (
        <>
          <p>
            Signature {savedSignatures.length + 1} of {TOTAL_SIGS}
          </p>

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
          

          <div className="btn-group">
            <button
              className="btn clear"
              onClick={() => {
                sigCanvas.current.clear();
                signatureStrokesRef.current = [];
              }}
            >
              Clear
            </button>

            {savedSignatures.length < TOTAL_SIGS && (
              <button className="btn save" onClick={saveOneSignature}>
                Save Signature
              </button>
            )}
          </div>

          {savedSignatures.length === TOTAL_SIGS && (
            <button
              className="btn submit"
              onClick={submitRegistration}
              disabled={loading}
            >
              {loading ? "Registering..." : "Submit Registration"}
            </button>
          )}
        </>
      )}

      {userId && (
        <div className="result">
          <h3>Registration Complete</h3>
          <p>Your User ID:</p>
          <strong>{userId}</strong>
        </div>
      )}

      {message && <p className="msg info">{message}</p>}
    </div>
  );
};

export default RegisterSignature;
