import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 300 },
    { duration: '1m', target: 300 },
    { duration: '30s', target: 0 },
  ],
};

const BASE = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  const res = http.get(`${BASE}/health`);
  check(res, { 'ok': (r) => r.status === 200 });
}
