import ws from 'k6/ws';
import { check } from 'k6';

export const options = {
  vus: 100,
  duration: '30s',
};

// Requires valid token and room — smoke test connection attempt
export default function () {
  const url = __ENV.WS_URL || 'ws://localhost:8000/api/v1/ws/chat/00000000-0000-0000-0000-000000000001?token=test';
  const res = ws.connect(url, {}, function (socket) {
    socket.on('open', () => socket.close());
    socket.setTimeout(() => socket.close(), 5000);
  });
  check(res, { 'connected or rejected': (r) => r && r.status >= 0 });
}
