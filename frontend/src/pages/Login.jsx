import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { apiError } from "../utils/financial";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [signup, setSignup] = useState(false);
  const [busy, setBusy] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);

    try {
      if (signup) await api.post("/auth/signup", { username, email, password });
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem("access_token", response.data.access_token);

      navigate("/");
    } catch (error) {
      setError(apiError(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form
        onSubmit={handleLogin}
        className="bg-white p-8 rounded-xl shadow-md w-full max-w-md"
      >
        <h1 className="text-3xl font-bold mb-2">Persona Wallet</h1>

        <p className="text-gray-500 mb-6">
          {signup
            ? "Create your financial wallet"
            : "Sign in to your financial wallet"}
        </p>
        {signup && (
          <label className="mb-4 block font-medium">
            Username
            <input
              className="mt-2 w-full rounded-lg border p-3"
              value={username}
              required
              minLength={3}
              maxLength={50}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
            />
          </label>
        )}

        <div className="mb-4">
          <label className="block mb-2 font-medium">Email</label>

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded-lg p-3"
            placeholder="you@example.com"
            required
          />
        </div>

        <div className="mb-4">
          <label className="block mb-2 font-medium">Password</label>

          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border rounded-lg p-3"
            placeholder="Password"
            required
          />
        </div>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full bg-blue-600 text-white p-3 rounded-lg font-semibold"
        >
          {busy ? "Please wait..." : signup ? "Create account" : "Login"}
        </button>
        <button
          type="button"
          disabled={busy}
          className="mt-5 w-full text-sm font-semibold text-blue-600"
          onClick={() => {
            setSignup(!signup);
            setError("");
          }}
        >
          {signup
            ? "Already have an account? Sign in"
            : "New here? Create an account"}
        </button>
      </form>
    </div>
  );
}

export default Login;
