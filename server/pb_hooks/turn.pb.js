/// <reference path="../pb_data/types.d.ts" />
// Временный пароль к ретранслятору видеозвонков (coturn, режим use-auth-secret).
// Выдаётся только тем, кто вошёл: репетитору или ученику. Живёт 6 часов, общий секрет на клиент не попадает.
// Секрет и адрес берутся из окружения сервиса: KLETKA_TURN_SECRET, KLETKA_TURN_HOST.
routerAdd("GET", "/api/kletka/turn", (e) => {
  const secret = $os.getenv("KLETKA_TURN_SECRET")
  const host = $os.getenv("KLETKA_TURN_HOST")
  if (!secret || !host) return e.json(404, { message: "turn off" })
  const lib = require(`${__hooks}/kletka_hmac.js`)
  const ttl = 6 * 3600
  const username = (Math.floor(Date.now() / 1000) + ttl) + ":" + e.auth.id
  return e.json(200, {
    urls: ["turn:" + host + ":3478?transport=udp", "turn:" + host + ":3478?transport=tcp"],
    username,
    credential: lib.hmacSha1Base64(secret, username),
    ttl,
  })
}, $apis.requireAuth())
