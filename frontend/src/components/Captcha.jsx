import "altcha";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function Captcha({ action }) {
  return (
    <altcha-widget name="captcha" challenge={`${BASE_URL}/captcha/${action}`} />
  );
}
