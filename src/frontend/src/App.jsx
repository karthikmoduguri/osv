import React, { useState } from "react";
import RegisterSignature from "./components/SignatureCanvas";
import VerifySignature from "./components/VerifySignature";

const App = () => {
  const [page, setPage] = useState("register");

  return (
    <div style={{ textAlign: "center", marginTop: 40 }}>

      <h1>Online Signature Verification System</h1>
                                                                                                
      {/* NAV BUTTONS */}
      <div style={{ marginBottom: 30 }}>
        <button
          onClick={() => setPage("register")}
          style={{
            padding: "10px 20px",
            marginRight: 15,
            background: page === "register" ? "#4CAF50" : "#ccc",
            color: "white",
            border: "none",
            cursor: "pointer"
          }}
        >
          Register
        </button>

        <button
          onClick={() => setPage("verify")}
          style={{
            padding: "10px 20px",
            background: page === "verify" ? "#2196F3" : "#ccc",
            color: "white",
            border: "none",
            cursor: "pointer"
          }}
        >
          Verify
        </button>
      </div>

      {/* PAGE RENDER */}
      {page === "register" && <RegisterSignature />}
      {page === "verify" && <VerifySignature />}

    </div>
  );
};

export default App;
