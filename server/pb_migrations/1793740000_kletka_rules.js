/// <reference path="../pb_data/types.d.ts" />
// Правила доступа после ревью 03.11.2026.
//   1. Репетитор не может переписать свою домашку или комнату на чужого ученика:
//      поля tutor и student после создания не меняются.
//   2. Ученик не может менять название домашки.
//   3. Пульс: запрет менять who и room действует и на репетитора (раньше скобки стояли неверно).
const student = "@request.body.payload:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.code:isset = false && @request.body.review:isset = false"
const fixed = "@request.body.tutor:isset = false && @request.body.student:isset = false"
const asSelf = "(room.tutor = @request.auth.id && who = 't') || (room.student = @request.auth.id && who = 's')"

migrate((app) => {
  const a = app.findCollectionByNameOrId("assignments")
  a.updateRule = `(tutor = @request.auth.id && ${fixed}) || (student = @request.auth.id && status != "done" && ${student} && @request.body.title:isset = false)`
  app.save(a)

  const r = app.findCollectionByNameOrId("rooms")
  r.updateRule = `(tutor = @request.auth.id && ${fixed}) || (student = @request.auth.id && @request.body.mats:isset = false && @request.body.st:isset = false && ${fixed} && @request.body.docs:isset = false)`
  app.save(r)

  const p = app.findCollectionByNameOrId("pulse")
  p.updateRule = `(${asSelf}) && @request.body.who:isset = false && @request.body.room:isset = false`
  app.save(p)
}, (app) => {
  const a = app.findCollectionByNameOrId("assignments")
  a.updateRule = `tutor = @request.auth.id || (student = @request.auth.id && status != "done" && ${student})`
  app.save(a)

  const r = app.findCollectionByNameOrId("rooms")
  r.updateRule = "tutor = @request.auth.id || (student = @request.auth.id && @request.body.mats:isset = false && @request.body.st:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.docs:isset = false)"
  app.save(r)

  const p = app.findCollectionByNameOrId("pulse")
  p.updateRule = asSelf + " && (@request.body.who:isset = false) && (@request.body.room:isset = false)"
  app.save(p)
})
