/// <reference path="../pb_data/types.d.ts" />
// Безопасность после проверки 28.10.2026.
//   1. Лимиты запросов считаются по настоящему адресу пользователя. Перед PocketBase стоит Caddy,
//      и без доверенного заголовка все запросы приходят с 127.0.0.1: один общий лимит на всех.
//      Тогда несколько уроков сразу упираются в лимит, сигналы звонка и пульс комнаты теряются.
//   2. Общий лимит на /api/ выше: в уроке пульс и ответы уходят часто, а ученики школы бывают за одним адресом.
//   3. Ученик не может менять сданную работу: ни результат, ни статус, ни фото.
migrate((app) => {
  const s = app.settings()
  s.trustedProxy.headers = ["X-Forwarded-For"]
  s.trustedProxy.useLeftmostIP = false
  for (const r of s.rateLimits.rules) if (r.label === "/api/") r.maxRequests = 1000
  app.save(s)

  const a = app.findCollectionByNameOrId("assignments")
  a.updateRule = "tutor = @request.auth.id || (student = @request.auth.id && status != \"done\" && @request.body.payload:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.code:isset = false && @request.body.review:isset = false)"
  app.save(a)
}, (app) => {
  const s = app.settings()
  s.trustedProxy.headers = []
  for (const r of s.rateLimits.rules) if (r.label === "/api/") r.maxRequests = 300
  app.save(s)

  const a = app.findCollectionByNameOrId("assignments")
  a.updateRule = "tutor = @request.auth.id || (student = @request.auth.id && @request.body.payload:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.code:isset = false && @request.body.review:isset = false)"
  app.save(a)
})
