/// <reference path="../pb_data/types.d.ts" />
// Фото выполненной работы: ученик фотографирует домашку на бумаге, репетитор смотрит и ставит отметку.
//   assignments.photos — снимки ученика (до 12, только картинки);
//   assignments.review — отметка и комментарий репетитора. Ученик её видит, но менять не может.
migrate((app) => {
  const a = app.findCollectionByNameOrId("assignments")
  a.fields.add(new FileField({ name: "photos", maxSelect: 12, maxSize: 12000000, protected: true, thumbs: ["240x0"],
    mimeTypes: ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"] }))
  a.fields.add(new JSONField({ name: "review", maxSize: 20000 }))
  a.updateRule = "tutor = @request.auth.id || (student = @request.auth.id && @request.body.payload:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.code:isset = false && @request.body.review:isset = false)"
  app.save(a)
}, (app) => {
  const a = app.findCollectionByNameOrId("assignments")
  a.fields.removeByName("photos")
  a.fields.removeByName("review")
  a.updateRule = "tutor = @request.auth.id || (student = @request.auth.id && @request.body.payload:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.code:isset = false)"
  app.save(a)
})
