import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '5m', target: 100 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASE = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  const res = http.get(`${BASE}/health`);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(0.1);
}
